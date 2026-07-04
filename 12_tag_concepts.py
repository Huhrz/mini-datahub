"""
步骤 9：批量给数据集打"概念标签"（语义对齐，写进 concept_tags 表）
=====================================================================

把目录里每个数据集的原始任务描述，对齐成统一概念 id，写进一张单独的
concept_tags 表。网页"按概念检索"直接读这张表 —— 重活（算向量）在这里一次跑完，
网页查询时就很快、不用实时算。

接入新数据后跑一次即可（先关网页避免数据库锁）：
    python 12_tag_concepts.py

需要 pip install sentence-transformers 才能用语义对齐；没装则只用规则对齐
（精确/模糊），能对上多少算多少。
"""

import json
import hub_data as hd

try:
    import taxonomy_semantic as aligner          # 优先语义
    MODE = "语义(embedding)+规则"
except Exception:
    import taxonomy as aligner                    # 退回纯规则
    MODE = "纯规则"


def main():
    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑 streamlit 的终端按 Ctrl+C 关闭网页再运行。")
            return
        raise

    con.execute("CREATE TABLE IF NOT EXISTS concept_tags "
                "(dataset_id VARCHAR, category VARCHAR, concept_id VARCHAR)")
    con.execute("DELETE FROM concept_tags WHERE category = 'tasks'")

    rows = con.execute("SELECT dataset_id, name, tasks FROM datasets").fetchall()
    print(f"对齐模式：{MODE}；共 {len(rows)} 个数据集\n")

    total_tags, tagged_ds, unresolved = 0, 0, 0
    for did, name, tasks_json in rows:
        try:
            raw = json.loads(tasks_json) if tasks_json else []
        except Exception:
            raw = []
        concepts = set()
        for t in raw:
            r = aligner.align(t, "tasks")
            if r:
                concepts.add(r["concept_id"])
            else:
                unresolved += 1
        for cid in concepts:
            con.execute("INSERT INTO concept_tags VALUES (?, 'tasks', ?)", [did, cid])
        total_tags += len(concepts)
        if concepts:
            tagged_ds += 1
        print(f"  {name:<40} -> {sorted(concepts) or '（未对齐到任何概念）'}")

    print(f"\n完成：{tagged_ds}/{len(rows)} 个数据集打上了概念标签，"
          f"共 {total_tags} 个标签；{unresolved} 个原始标签未对齐（可加进词表或调阈值）。")
    print("现在刷新网页，用「🧭 按任务概念检索」就能跨命名检索了。")
    con.close()


if __name__ == "__main__":
    main()
