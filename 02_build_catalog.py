"""
步骤 2：把元数据抽进 DuckDB 目录，并做检索
=============================================

演示 DataHub 的"检索台"：
  - 把几个数据集 + 它们的轨迹元数据写进 DuckDB
  - 跑几条示例查询，体现"按本体 / 许可 / 失败标注 筛选"的能力

默认用内置的几条样例元数据（不联网即可跑）。真实接入时，把
build_sample_metadata() 换成"从 LeRobotDataset 读取并填 schema"即可。

运行：
    python 02_build_catalog.py
"""

import duckdb
from schema import CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE
# 样例数据与插入逻辑集中放在 hub_data 里，命令行和网页共用同一份，避免不一致
from hub_data import build_sample_metadata, insert_datasets, insert_episodes

DB_PATH = "catalog.duckdb"


def main():
    con = duckdb.connect(DB_PATH)
    con.execute("DROP TABLE IF EXISTS datasets; DROP TABLE IF EXISTS episodes;")
    con.execute(CREATE_DATASETS_TABLE)
    con.execute(CREATE_EPISODES_TABLE)

    datasets, episodes = build_sample_metadata()
    insert_datasets(con, datasets)
    insert_episodes(con, episodes)
    print(f"[ok] 已写入 {len(datasets)} 个数据集、{len(episodes)} 条轨迹到 {DB_PATH}\n")

    # ---------- 示例检索 ----------
    def show(title, sql):
        print(f"—— {title} ——")
        print(con.execute(sql).df().to_string(index=False))
        print()

    show("① 全部数据集概览",
         "SELECT name, embodiment, license_spdx, commercial_ok, provenance_type, n_episodes "
         "FROM datasets ORDER BY n_episodes DESC")

    show("② 只要【可商用】的数据集（合规过滤，DataHub 的差异化能力）",
         "SELECT name, license_spdx FROM datasets WHERE commercial_ok = TRUE")

    show("③ 找【双臂或人形】本体的数据集",
         "SELECT name, embodiment, robot_model, dof FROM datasets WHERE embodiment IN ('bimanual','humanoid')")

    show("④ 找【带失败标注】的数据集（高价值数据）",
         "SELECT name FROM datasets WHERE has_failure_labels = TRUE")

    show("⑤ 各数据集的动作约定（文档 4.3：只描述不强转）",
         "SELECT name, action_convention FROM datasets")

    show("⑥ 跨数据集：列出所有【失败】的轨迹",
         "SELECT episode_uid, task_text FROM episodes WHERE success = FALSE")

    show("⑦ 统计：按本体汇总可用轨迹数（为'多样性配比'打基础）",
         "SELECT embodiment, COUNT(*) AS n_datasets, SUM(n_episodes) AS total_episodes "
         "FROM datasets GROUP BY embodiment ORDER BY total_episodes DESC")

    con.close()


if __name__ == "__main__":
    main()
