"""
步骤 8：批量自动接入（从 HuggingFace 枚举一堆真实数据集）
==========================================================

不再手动一个个敲 ID，而是用 HF API 一次列出几十个真实 LeRobot 数据集，
逐个抓元数据（含任务描述）入库。让目录从几个样例 → 几十上百个真实数据集，
正好用来检验 taxonomy 的"按概念检索"在规模下好不好使。

这是文档"联邦优先"的体现：只拉元数据、不下数据本体，所以接 5 个和接 100 个都很快。

需要联网。用法：
    python 11_batch_ingest.py --author lerobot --limit 40
    python 11_batch_ingest.py --task robotics --limit 40   # 按任务类别枚举（更广）

跑完刷新网页，用左侧"🧭 按任务概念检索"试试效果。
"""

import argparse
import sources
import hub_data as hd
from schema import CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE, insert_sql, to_db_values

INSERT_DATASET = insert_sql("datasets", hd.DatasetMeta)


def list_repo_ids(author, task, limit):
    from huggingface_hub import HfApi
    api = HfApi()
    kwargs = {"limit": limit * 3}        # 多取些，因为部分会抓取失败被跳过
    if author:
        kwargs["author"] = author
    if task:
        kwargs["filter"] = f"task_categories:{task}"
    return [d.id for d in api.list_datasets(**kwargs)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default="lerobot", help="按账号枚举（默认 lerobot）")
    ap.add_argument("--task", default=None, help="按任务类别枚举，如 robotics（与 --author 二选一更广）")
    ap.add_argument("--limit", type=int, default=40, help="最多成功接入多少个")
    args = ap.parse_args()

    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑 streamlit 的终端按 Ctrl+C 关闭网页再运行。")
            return
        raise
    con.execute(CREATE_DATASETS_TABLE)
    con.execute(CREATE_EPISODES_TABLE)

    repo_ids = list_repo_ids(args.author, args.task, args.limit)
    print(f"枚举到 {len(repo_ids)} 个候选，开始接入（目标成功 {args.limit} 个）…\n")

    ok = 0
    for rid in repo_ids:
        if ok >= args.limit:
            break
        try:
            meta = sources.fetch("lerobot_hf", rid)
            if meta.n_episodes == 0:          # 没有标准 LeRobot 结构的跳过
                raise ValueError("无 episodes，疑似非轨迹数据集")
            con.execute("DELETE FROM datasets WHERE dataset_id = ?", [meta.dataset_id])
            con.execute(INSERT_DATASET, to_db_values(meta))
            ok += 1
            print(f"[{ok:>3}] {rid:<45} {meta.embodiment:<11} {meta.n_episodes} eps  tasks={len(meta.tasks)}")
        except Exception as e:
            print(f"[skip] {rid:<45} {repr(e)[:60]}")

    total = con.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
    print(f"\n成功接入 {ok} 个；目录现共有 {total} 个数据集。")
    print("刷新网页，用左侧「🧭 按任务概念检索」检验 taxonomy 在规模下的效果。")
    con.close()


if __name__ == "__main__":
    main()
