"""
步骤 9：给数据集打"概念标签"（覆盖度地图靠这张表）
====================================================

优先用**语义向量**把每个数据集分到最接近的任务概念——每个数据集至少落一个概念，
覆盖度地图不再大面积空白。没有向量/没装模型时，退回"逐条任务规则对齐"（召回低）。

先关后端避免数据库锁：
    python 12_tag_concepts.py

依赖：先跑过 13_build_embeddings.py（有 dataset_embeddings 向量）效果最好。
"""

import json
import hub_data as hd


def main():
    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑后端的终端按 Ctrl+C 关闭再运行。")
            return
        raise

    # 首选：语义向量分配（覆盖全、分得准）
    try:
        import embeddings
        has_vec = con.execute("SELECT COUNT(*) FROM dataset_embeddings").fetchone()[0] > 0 \
            if _table_exists(con, "dataset_embeddings") else False
        if has_vec:
            n = embeddings.assign_concepts(con)
            if n > 0:
                _report(con)
                con.close()
                return
    except Exception as e:
        print(f"[concepts] 语义打标不可用，退回规则对齐：{repr(e)[:80]}")

    # 退回：逐条任务的规则对齐
    import taxonomy as tx
    con.execute("CREATE TABLE IF NOT EXISTS concept_tags "
                "(dataset_id VARCHAR, category VARCHAR, concept_id VARCHAR)")
    con.execute("DELETE FROM concept_tags WHERE category = 'tasks'")
    rows = con.execute("SELECT dataset_id, tasks FROM datasets").fetchall()
    for did, tasks_json in rows:
        try:
            raw = json.loads(tasks_json) if tasks_json else []
        except Exception:
            raw = []
        concepts, _ = tx.align_many(raw, "tasks")
        for cid in concepts:
            con.execute("INSERT INTO concept_tags VALUES (?, 'tasks', ?)", [did, cid])
    _report(con)
    con.close()


def _table_exists(con, name):
    try:
        con.execute(f"SELECT 1 FROM {name} LIMIT 1")
        return True
    except Exception:
        return False


def _report(con):
    tagged = con.execute(
        "SELECT COUNT(DISTINCT dataset_id) FROM concept_tags WHERE category='tasks'").fetchone()[0]
    total = con.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    print(f"完成：{tagged}/{total} 个数据集有了概念标签。刷新网页看覆盖度地图。")


if __name__ == "__main__":
    main()
