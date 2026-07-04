"""
步骤 7：taxonomy 对齐 demo（B1 护城河演示）
============================================

两件事：
  1) 把各源五花八门的原始标签，对齐到统一概念 —— 证明 grasp / pick-and-place /
     抓取 会被归到同一个概念 id（这就是跨数据集检索能"准"的根本）。
  2) 在目录上做"按概念检索"：搜一个概念，把所有【叫法不同但本质相同】的数据集都找出来。

不联网即可运行：
    python 10_align_taxonomy.py
"""

import taxonomy as tx
import hub_data as hd
import json


def demo_align():
    print(f"== 受控词表版本 {tx.VERSION}：对齐各源杂乱标签 ==\n")
    raw_tasks = ["grasp", "pick-and-place", "抓取", "peg insertion", "插入",
                 "push the T block", "fold clothes", "叠衣服", "open the drawer",
                 "某个没见过的任务"]
    print(f"{'原始标签':<20}{'对齐到概念':<16}{'置信度':<8}{'方式'}")
    for raw in raw_tasks:
        r = tx.align(raw, "tasks")
        if r:
            print(f"{raw:<18}{r['concept_id']:<16}{r['confidence']:<8}{r['matched_by']}")
        else:
            print(f"{raw:<18}{'❓ 需人工复核':<16}{'-':<8}-")
    print("\n关键点：grasp / pick-and-place / 抓取 都归到了 pick_place —— "
          "叫法不同，概念统一。匹配不上的自动标记'需人工复核'（半自动+人工兜底）。\n")


def demo_concept_search():
    print("== 在目录上'按概念检索'（跨命名）==\n")
    con = hd.ensure_catalog()
    rows = con.execute("SELECT dataset_id, name, tasks FROM datasets").fetchall()

    # 为每个数据集把原始 tasks 对齐成概念 id 集合
    ds_concepts = {}
    for did, name, tasks_json in rows:
        try:
            raw = json.loads(tasks_json) if tasks_json else []
        except Exception:
            raw = []
        aligned, _ = tx.align_many(raw, "tasks")
        ds_concepts[name] = aligned

    # 模拟用户搜"抓取"——先对齐查询，再按概念 id 匹配
    for query in ["抓取", "assembly"]:
        q = tx.align(query, "tasks")
        if not q:
            print(f"查询「{query}」未对齐到已知概念\n")
            continue
        cid = q["concept_id"]
        hits = [name for name, cs in ds_concepts.items() if cid in cs]
        print(f"搜「{query}」→ 概念 {cid} → 命中数据集: {hits or '无'}")
    con.close()
    print("\n意义：用户用任意叫法搜，都能命中概念相同的数据集 —— "
          "这是普通字符串匹配做不到的，也是 HF 那种通用平台没有的能力。")


if __name__ == "__main__":
    demo_align()
    demo_concept_search()
