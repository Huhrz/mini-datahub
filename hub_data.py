"""
数据层 —— 给网页(app.py)和命令行(02)共用的"目录读写"逻辑
============================================================

把所有跟 DuckDB 打交道的逻辑集中在这里。不依赖 Streamlit，可单独测试。
已对齐升级后的 Catalog Entry schema（schema.py）。
"""

import os
import duckdb
from schema import (
    DatasetMeta, EpisodeMeta, license_fields,
    CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE,
    insert_sql, to_db_values,
)

# 数据库路径可用环境变量覆盖（Docker 挂卷 / 换库时用）
DB_PATH = os.environ.get("MDH_DB", "catalog.duckdb")

INSERT_DATASET = insert_sql("datasets", DatasetMeta)
INSERT_EPISODE = insert_sql("episodes", EpisodeMeta)


# ---------------- 样例数据（首次运行的演示内容）----------------
def build_sample_metadata():
    """造几个有代表性的样例目录项（含不同本体 / 许可 / 动作约定 / 失败标注）。"""
    datasets, episodes = [], []
    # (id, name, source, fmt, license, n_ep, fps, embodiment, robot, dof, arms,
    #  end_effector, base, prov, cams, failures, act_conv, tasks, scenes, modalities)
    specs = [
        # 末尾 home = 各数据集真实存在的页面（避免 404）
        ("lerobot/aloha_sim_insertion_human", "ALOHA Sim Insertion", "huggingface", "lerobot_v3",
         "apache-2.0", 50, 50.0, "bimanual", "aloha", 14, 2, "gripper", "fixed", "sim", 1, False,
         {"space": "joint", "frame": "base", "abs_or_delta": "abs", "units": "rad"},
         ["insertion", "pick_place"], ["tabletop"], ["rgb", "state"], 0.94, 0.61,
         "https://huggingface.co/datasets/lerobot/aloha_sim_insertion_human"),
        ("agibot-world/AgiBotWorld-Alpha", "AgiBot World", "agibot", "lerobot_v3",
         "cc-by-nc-sa-4.0", 100, 30.0, "humanoid", "agibot_g2", 28, 2, "dexterous_hand", "mobile", "teleop", 4, False,
         {"space": "joint", "frame": "base", "abs_or_delta": "abs", "units": "rad"},
         ["pick_place", "long_horizon"], ["home", "commercial"], ["rgb", "depth", "state", "language"], 0.90, 0.72,
         "https://huggingface.co/datasets/agibot-world/AgiBotWorld-Alpha"),
        ("x-humanoid/RoboMIND", "RoboMIND", "robomind", "hdf5",
         "cc-by-4.0", 80, 25.0, "single_arm", "franka", 7, 1, "gripper", "fixed", "teleop", 3, True,
         {"space": "ee_pose", "frame": "base", "abs_or_delta": "delta", "units": "m+quat"},
         ["pick_place", "manipulation"], ["tabletop", "kitchen"], ["rgb", "state"], 0.88, 0.55,
         "https://x-humanoid-robomind.github.io/"),
        ("google/rt_1", "RT-1 (OpenX)", "openx", "rlds",
         "apache-2.0", 70, 3.0, "single_arm", "everyday_robot", 7, 1, "gripper", "mobile", "teleop", 1, False,
         {"space": "ee_pose", "frame": "base", "abs_or_delta": "delta", "units": "m+rpy"},
         ["pick_place", "navigation"], ["office", "kitchen"], ["rgb", "language"], 0.82, 0.40,
         "https://robotics-transformer-x.github.io/"),
        ("lerobot/pusht", "PushT", "huggingface", "lerobot_v3",
         "apache-2.0", 206, 10.0, "single_arm", "2d_pointer", 2, 1, "none", "fixed", "teleop", 1, False,
         {"space": "ee_pos2d", "frame": "world", "abs_or_delta": "abs", "units": "px"},
         ["pushing"], ["tabletop_2d"], ["rgb", "state"], 0.97, 0.51,
         "https://huggingface.co/datasets/lerobot/pusht"),
    ]
    for (did, name, src, fmt, lic, n_ep, fps, emb, robot, dof, arms, eef, base, prov,
         cams, fail, act_conv, tasks, scenes, mods, q_score, l_score, home) in specs:
        spdx, com_ok, redist_ok = license_fields(lic)
        datasets.append(DatasetMeta(
            dataset_id=did, name=name, source=src,
            source_uri=home, source_format=fmt,
            license_spdx=spdx, commercial_ok=com_ok, redistribute_ok=redist_ok,
            quality_score=q_score, learnability_score=l_score, provenance_type=prov,
            embodiment=emb, robot_model=robot, dof=dof, arms=arms,
            end_effector=eef, base=base, action_convention=act_conv,
            tasks=tasks, scenes=scenes, modalities=mods,
            fps=fps, n_cameras=cams, n_episodes=n_ep, total_frames=n_ep * 120,
            duration_s=n_ep * 120 / fps, has_failure_labels=fail,
            linked_benchmarks=(["LIBERO"] if emb != "humanoid" else []),
            homepage=home,
        ))
        for i in range(min(n_ep, 5)):
            success = (i % 4 != 0) if fail else None
            episodes.append(EpisodeMeta(
                episode_uid=f"{did}#{i}", dataset_id=did, episode_index=i,
                length=120, duration_s=120 / fps,
                task_text=f"sample task {i} on {robot}",
                embodiment=emb, success=success,
                action_dim=dof, state_dim=dof,
            ))
    return datasets, episodes


# ---------------- 连接 & 初始化（经 store 抽象，支持 DuckDB / Postgres）----------------
import store


def get_connection(db_path=None, read_only=False):
    return store.connect(read_only=read_only)


def _table_empty(con, table):
    row = store.one(con, f"SELECT COUNT(*) FROM {table}")
    return (row is None) or (row[0] == 0)


def _has_column(con, table, col):
    return store.has_column(con, table, col)


def _migrate_columns(con, table, dc):
    """加列不删表：为已存在的表补齐 dataclass 里新增的字段（**保留数据**）。
    新字段一律追加在 dataclass 末尾，ALTER 也追加在表末尾，列序保持一致，
    定位插入(positional INSERT)不会错位。"""
    from dataclasses import fields as dc_fields
    from schema import _col_type
    cols = set(store.table_columns(con, table))
    if not cols:
        return                    # 表不存在，交给 CREATE 处理
    for f in dc_fields(dc):
        if f.name not in cols:
            store.run(con, store.ddl(
                f"ALTER TABLE {table} ADD COLUMN {f.name} {_col_type(f.type)}"))


def insert_datasets(con, datasets):
    store.run_many(con, INSERT_DATASET, [to_db_values(d) for d in datasets])


def insert_episodes(con, episodes):
    store.run_many(con, INSERT_EPISODE, [to_db_values(e) for e in episodes])


def ensure_catalog(db_path=None):
    """确保目录存在且非空；为空则灌入样例数据。返回连接。"""
    con = store.connect()
    store.run(con, store.ddl(CREATE_DATASETS_TABLE))
    store.run(con, store.ddl(CREATE_EPISODES_TABLE))
    # 新增字段用"加列"迁移，绝不丢表——保住已接入的数据
    _migrate_columns(con, "datasets", DatasetMeta)
    _migrate_columns(con, "episodes", EpisodeMeta)
    if _table_empty(con, "datasets"):
        datasets, episodes = build_sample_metadata()
        insert_datasets(con, datasets)
        insert_episodes(con, episodes)
    return con


# ---------------- 查询 ----------------
def query_datasets(con, search="", embodiments=None, formats=None, provenances=None,
                   commercial_only=False, failures_only=False, min_episodes=0, min_quality=0.0):
    sql = "SELECT * FROM datasets WHERE 1=1"
    params = []
    if min_quality and min_quality > 0:
        sql += " AND quality_score >= ?"
        params.append(float(min_quality))
    if search:
        # 名称 / ID / 任务描述 / 机器人型号 都参与匹配，让"搜内容"真正好用
        sql += (" AND (lower(name) LIKE ? OR lower(dataset_id) LIKE ? "
                "OR lower(tasks) LIKE ? OR lower(robot_model) LIKE ?)")
        kw = f"%{search.lower()}%"
        params += [kw, kw, kw, kw]
    if embodiments:
        sql += f" AND embodiment IN ({','.join(['?']*len(embodiments))})"
        params += list(embodiments)
    if formats:
        sql += f" AND source_format IN ({','.join(['?']*len(formats))})"
        params += list(formats)
    if provenances:
        sql += f" AND provenance_type IN ({','.join(['?']*len(provenances))})"
        params += list(provenances)
    if commercial_only:
        sql += " AND commercial_ok = TRUE"
    if failures_only:
        sql += " AND has_failure_labels = TRUE"
    if min_episodes:
        sql += " AND n_episodes >= ?"
        params.append(int(min_episodes))
    sql += " ORDER BY n_episodes DESC"
    return store.run_df(con, sql, params)


def get_episodes(con, dataset_id):
    return store.run_df(con,
        "SELECT episode_index, task_text, success, length, duration_s, action_dim, state_dim "
        "FROM episodes WHERE dataset_id = ? ORDER BY episode_index", [dataset_id])


def distinct_values(con, column):
    try:
        rows = store.run(con, f"SELECT DISTINCT {column} FROM datasets "
                              f"WHERE {column} IS NOT NULL AND {column} != '' "
                              f"ORDER BY {column}")
        return [r[0] for r in rows]
    except Exception:
        return []


def summary_stats(con):
    row = store.one(con,
        "SELECT COUNT(*) AS n_datasets, COALESCE(SUM(n_episodes),0) AS n_episodes, "
        "COALESCE(SUM(total_frames),0) AS n_frames FROM datasets")
    return {"n_datasets": row[0], "n_episodes": row[1], "n_frames": row[2]}


def by_embodiment(con):
    return store.run_df(con,
        "SELECT embodiment, SUM(n_episodes) AS episodes FROM datasets "
        "GROUP BY embodiment ORDER BY episodes DESC")


def hf_visualizer_url(dataset_id):
    return f"https://huggingface.co/spaces/lerobot/visualize_dataset?dataset={dataset_id}"
