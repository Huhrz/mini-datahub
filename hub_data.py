"""
数据层 —— 给网页(app.py)和命令行(02)共用的"目录读写"逻辑
============================================================

把所有跟 DuckDB 打交道的逻辑集中在这里，好处是：
  - 网页只管显示，不用关心数据库细节
  - 这一层不依赖 Streamlit，可以单独测试

主要函数：
  - get_connection(db)      连接（或新建）目录数据库
  - ensure_catalog(db)      若目录为空，自动灌入一批样例数据（首次演示用）
  - build_sample_metadata() 造样例数据集 + 轨迹
  - query_datasets(con, ...) 按条件筛选数据集
  - get_episodes(con, id)   取某数据集的轨迹
  - hf_visualizer_url(id)    生成"在线可视化"链接
"""

import os
import duckdb
from schema import (
    DatasetMeta, EpisodeMeta, infer_commercial_use,
    CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE,
)

DB_PATH = "catalog.duckdb"


# ---------------- 样例数据（首次运行的演示内容）----------------
def build_sample_metadata():
    """造几个有代表性的样例数据集（含不同本体 / 许可 / 失败标注）。"""
    datasets, episodes = [], []
    specs = [
        # (id, name, source, fmt, license, n_ep, fps, embodiment, robot, cams, failures, collection)
        ("lerobot/aloha_sim_insertion", "ALOHA Sim Insertion", "huggingface", "lerobot_v3",
         "apache-2.0", 50, 50.0, "bimanual", "aloha", 1, False, "sim"),
        ("agibot-world/AgiBotWorld", "AgiBot World", "agibot", "lerobot_v3",
         "cc-by-nc-sa-4.0", 100, 30.0, "humanoid", "agibot_g2", 4, False, "teleop"),
        ("x-humanoid/RoboMIND", "RoboMIND", "robomind", "hdf5",
         "cc-by-4.0", 80, 25.0, "single_arm", "franka", 3, True, "teleop"),
        ("google/rt_1", "RT-1 (OpenX)", "openx", "rlds",
         "apache-2.0", 70, 3.0, "single_arm", "everyday_robot", 1, False, "teleop"),
        ("lerobot/pusht", "PushT", "huggingface", "lerobot_v3",
         "apache-2.0", 206, 10.0, "single_arm", "2d_pointer", 1, False, "teleop"),
    ]
    for (did, name, src, fmt, lic, n_ep, fps, emb, robot, cams, fail, coll) in specs:
        datasets.append(DatasetMeta(
            dataset_id=did, name=name, source=src, source_format=fmt,
            license=lic, commercial_use=infer_commercial_use(lic),
            n_episodes=n_ep, total_frames=n_ep * 120, fps=fps,
            embodiment=emb, robot_model=robot, n_cameras=cams,
            has_failure_labels=fail, collection=coll,
            homepage=f"https://huggingface.co/datasets/{did}",
        ))
        for i in range(min(n_ep, 5)):
            success = (i % 4 != 0) if fail else None
            episodes.append(EpisodeMeta(
                episode_uid=f"{did}#{i}", dataset_id=did, episode_index=i,
                length=120, duration_s=120 / fps,
                task_text=f"sample task {i} on {robot}",
                embodiment=emb, success=success,
                action_dim=14 if emb == "bimanual" else 7,
                state_dim=14 if emb == "bimanual" else 7,
            ))
    return datasets, episodes


# ---------------- 连接 & 初始化 ----------------
def get_connection(db_path=DB_PATH, read_only=False):
    con = duckdb.connect(db_path, read_only=read_only)
    return con


def _table_empty(con, table):
    try:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    except Exception:
        return True


def ensure_catalog(db_path=DB_PATH):
    """确保目录存在且非空；为空则灌入样例数据。返回连接。"""
    con = get_connection(db_path)
    con.execute(CREATE_DATASETS_TABLE)
    con.execute(CREATE_EPISODES_TABLE)
    if _table_empty(con, "datasets"):
        datasets, episodes = build_sample_metadata()
        con.executemany(
            "INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [tuple(d.to_row().values()) for d in datasets],
        )
        con.executemany(
            "INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?,?)",
            [tuple(e.to_row().values()) for e in episodes],
        )
    return con


# ---------------- 查询 ----------------
def query_datasets(con, search="", embodiments=None, formats=None,
                   commercial_only=False, failures_only=False, min_episodes=0):
    """按条件筛选数据集，返回 DataFrame。"""
    sql = "SELECT * FROM datasets WHERE 1=1"
    params = []
    if search:
        sql += " AND (lower(name) LIKE ? OR lower(dataset_id) LIKE ?)"
        params += [f"%{search.lower()}%", f"%{search.lower()}%"]
    if embodiments:
        sql += f" AND embodiment IN ({','.join(['?']*len(embodiments))})"
        params += list(embodiments)
    if formats:
        sql += f" AND source_format IN ({','.join(['?']*len(formats))})"
        params += list(formats)
    if commercial_only:
        sql += " AND commercial_use = TRUE"
    if failures_only:
        sql += " AND has_failure_labels = TRUE"
    if min_episodes:
        sql += " AND n_episodes >= ?"
        params.append(int(min_episodes))
    sql += " ORDER BY n_episodes DESC"
    return con.execute(sql, params).df()


def get_episodes(con, dataset_id):
    return con.execute(
        "SELECT episode_index, task_text, success, length, duration_s, action_dim, state_dim "
        "FROM episodes WHERE dataset_id = ? ORDER BY episode_index", [dataset_id]
    ).df()


def distinct_values(con, column):
    try:
        rows = con.execute(f"SELECT DISTINCT {column} FROM datasets ORDER BY {column}").fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def summary_stats(con):
    row = con.execute(
        "SELECT COUNT(*) AS n_datasets, COALESCE(SUM(n_episodes),0) AS n_episodes, "
        "COALESCE(SUM(total_frames),0) AS n_frames FROM datasets"
    ).fetchone()
    return {"n_datasets": row[0], "n_episodes": row[1], "n_frames": row[2]}


def by_embodiment(con):
    return con.execute(
        "SELECT embodiment, SUM(n_episodes) AS episodes FROM datasets "
        "GROUP BY embodiment ORDER BY episodes DESC"
    ).df()


def hf_visualizer_url(dataset_id):
    """HuggingFace 官方的在线 LeRobot 可视化器链接（仅对 HF 上的数据集有效）。"""
    return f"https://huggingface.co/spaces/lerobot/visualize_dataset?dataset={dataset_id}"
