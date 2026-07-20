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


# 一批真实的机器人数据"多家来源"（HuggingFace 上的机构/团队账号）
DEFAULT_AUTHORS = [
    "lerobot",        # HuggingFace 官方 LeRobot
    "agibot-world",   # 智元 AgiBot World
    "x-humanoid",     # RoboMIND
    "nvidia",         # NVIDIA PhysicalAI / GR00T
    "youliangtan",    # OpenX 转 LeRobot 镜像
    "HuggingFaceVLA", # VLA 相关
    "openvla",        # OpenVLA
]


def list_repo_ids(authors, task, limit):
    from huggingface_hub import HfApi
    api = HfApi()
    if task:
        # 按任务类别枚举——覆盖全平台所有上传者（最"多家"）
        return [d.id for d in api.list_datasets(filter=f"task_categories:{task}", limit=limit * 3)]
    ids = []
    per = max(20, (limit * 3) // max(1, len(authors)))
    for a in authors:
        try:
            got = [d.id for d in api.list_datasets(author=a, limit=per)]
            print(f"  来源 {a}: 枚举到 {len(got)} 个")
            ids += got
        except Exception as e:
            print(f"  来源 {a}: 枚举失败 {repr(e)[:60]}")
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--authors", default=",".join(DEFAULT_AUTHORS),
                    help="多家来源账号(逗号分隔)，默认接 lerobot/agibot-world/x-humanoid/nvidia 等多家")
    ap.add_argument("--task", default=None, help="改用任务类别枚举(如 robotics)，覆盖全平台所有上传者")
    ap.add_argument("--limit", type=int, default=100, help="最多成功接入多少个")
    ap.add_argument("--workers", type=int, default=16, help="并发抓取线程数（越大越快，默认16）")
    args = ap.parse_args()
    authors = [a.strip() for a in args.authors.split(",") if a.strip()]

    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑 streamlit 的终端按 Ctrl+C 关闭网页再运行。")
            return
        raise
    import store
    store.run(con, store.ddl(CREATE_DATASETS_TABLE))
    store.run(con, store.ddl(CREATE_EPISODES_TABLE))

    src = f"任务类别={args.task}" if args.task else f"多家来源={authors}"
    print(f"枚举来源（{src}）…")
    repo_ids = list_repo_ids(authors, args.task, args.limit)
    # 去重，保持顺序；只取够用的候选（成功率约 30-60%）
    seen = set(); repo_ids = [x for x in repo_ids if not (x in seen or seen.add(x))]
    repo_ids = repo_ids[: args.limit * 3]
    print(f"共 {len(repo_ids)} 个候选，用 {args.workers} 并发抓取（目标成功 {args.limit} 个）…\n")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch_one(rid):
        try:
            meta = sources.fetch("lerobot_hf", rid)
            if meta.n_episodes == 0:
                return (rid, None, "无 episodes，疑似非轨迹数据集")
            return (rid, meta, None)
        except Exception as e:
            return (rid, None, repr(e)[:60])

    # 并发抓取（网络 I/O），数据库写入仍在主线程串行 -> 快且安全
    # 用 try/finally：无论正常跑完还是 Ctrl+C 中断，都会对已接入数据补向量+打标
    ok = 0
    try:
        ex = ThreadPoolExecutor(max_workers=args.workers)
        futures = [ex.submit(fetch_one, rid) for rid in repo_ids]
        for fut in as_completed(futures):
            if ok >= args.limit:
                continue
            rid, meta, err = fut.result()
            if meta:
                store.run(con, "DELETE FROM datasets WHERE dataset_id = ?", [meta.dataset_id])
                store.run(con, INSERT_DATASET, to_db_values(meta))
                ok += 1
                print(f"[{ok:>3}] {rid:<45} {meta.embodiment:<11} {meta.n_episodes} eps  tasks={len(meta.tasks)}")
            else:
                print(f"[skip] {rid:<45} {err}")
    except KeyboardInterrupt:
        print("\n[中断] 停止抓取——但已接入的数据仍会自动补向量+概念标签，请稍候…")
    finally:
        try:
            ex.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        total = store.one(con, "SELECT COUNT(*) FROM datasets")[0]
        print(f"\n成功接入 {ok} 个；目录现共有 {total} 个数据集。")
        # 自动补算语义向量(增量) + 重刷概念标签(覆盖度地图)；没装模型会安全跳过
        try:
            import embeddings
            embeddings.embed_missing(con, quiet=False)
            embeddings.assign_concepts(con, quiet=False)
        except Exception as e:
            print(f"[embeddings] 跳过：{repr(e)[:80]}")
        print("完成。重启后端 uvicorn 即可看到更新（搜索/覆盖度地图）。")

    print("刷新网页即可搜索（含跨语言语义搜索，若已装 sentence-transformers）。")
    con.close()


if __name__ == "__main__":
    main()
