"""
批量接入 Open X-Embodiment（跨源深化 —— 真正的多源）
=====================================================

把 OXE 登记表里的 ~58 个数据集（GCS 上的 RLDS，**不在 HuggingFace**）批量接入目录。
每个只拉几 KB 的 dataset_info.json（联邦：不下 tfrecord），合并登记表得到富元数据。

这是"跨源整合"的实证：接完后目录里同时有 HF/LeRobot 与 OXE/RLDS 两大异构源，
在同一 schema 下可检索、可筛选、可对齐 taxonomy、可比。

用法（DuckDB 需先停后端；Postgres 可并发）：
    python 17_ingest_oxe.py                 # 接入全部登记数据集
    python 17_ingest_oxe.py --limit 10      # 先接 10 个试试
    python 17_ingest_oxe.py --names fractal20220817_data,bc_z
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import sources
import oxe_registry as R
import hub_data as hd
import store

# gresearch 桶上 OXE 的常见版本号（逐个试，命中即用）
_VERSIONS = ["0.1.0", "0.1.1", "1.0.0"]


def fetch_one(name, versions):
    for v in versions:
        try:
            return sources.fetch("openx_rlds", f"{name}@{v}")
        except Exception:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default="", help="逗号分隔的数据集名（默认全部登记表）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--versions", default=",".join(_VERSIONS), help="逗号分隔的候选版本")
    args = ap.parse_args()

    names = [n for n in args.names.split(",") if n.strip()] or R.all_names()
    if args.limit:
        names = names[:args.limit]
    versions = [v for v in args.versions.split(",") if v.strip()]
    print(f"准备接入 {len(names)} 个 OXE 数据集（并发拉取 dataset_info.json）…")

    con = hd.ensure_catalog()

    def work(n):
        return n, fetch_one(n, versions)

    metas = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(work, names))

    ok = 0
    try:
        for name, meta in results:
            if meta is None:
                print(f"  [skip] {name}: 取不到 dataset_info.json（版本/命名不符或网络）")
                continue
            store.run(con, "DELETE FROM datasets WHERE dataset_id = ?", [meta.dataset_id])
            hd.insert_datasets(con, [meta])
            ok += 1
            gb = meta.size_bytes / 1e9 if meta.size_bytes else 0
            print(f"  [ok] {meta.dataset_id:<48} {meta.embodiment:<10} "
                  f"{meta.n_episodes:>7} eps  {gb:5.1f} GB  {'/'.join(meta.modalities)}")
    finally:
        print(f"\n成功接入 {ok}/{len(names)} 个 OXE 数据集。补语义向量 + 概念标签…")
        try:
            import embeddings
            embeddings.embed_missing(con, quiet=False)
            embeddings.assign_concepts(con)
        except Exception as e:
            print(f"[embeddings] 跳过：{repr(e)[:80]}")
        store.close(con)


if __name__ == "__main__":
    main()
