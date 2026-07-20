"""
元数据回填（enrich）—— 给已接入的数据集补更具体的规格
========================================================

分两部分：
  1) 派生量（免联网、对全部数据集瞬间生效）：
       duration_s        = total_frames / fps
       avg_episode_frames = total_frames / n_episodes
  2) 源侧规格（联网，仅 HF/LeRobot；结果写回，只补尚未补过的）：
       size_bytes / last_modified / downloads / likes（一次 dataset_info）
       video_resolution / video_codec（读 meta/info.json）

用法（DuckDB 需先停后端；Postgres 可并发）：
    python 16_enrich_metadata.py            # 派生量 + HF 规格回填
    python 16_enrich_metadata.py --derived-only   # 只补派生量（不联网）
    python 16_enrich_metadata.py --limit 50 --force
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import store
import sources
import hub_data as hd


def _is_hf(source, fmt):
    return source == "huggingface" or "lerobot" in str(fmt or "")


def enrich_hf(repo_id):
    """联网取 HF 规格：大小/更新时间/热度 + 分辨率/编码。"""
    out = sources._hf_meta(repo_id)
    res, codec = "", ""
    try:
        from huggingface_hub import hf_hub_download
        info = json.load(open(hf_hub_download(repo_id, "meta/info.json", repo_type="dataset")))
        res, codec = sources._video_specs(info.get("features", {}))
    except Exception:
        pass
    out["video_resolution"] = res
    out["video_codec"] = codec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived-only", action="store_true", help="只补派生量，不联网")
    ap.add_argument("--force", action="store_true", help="即使已补过也重新联网回填")
    ap.add_argument("--limit", type=int, default=0, help="最多联网回填多少个(0=不限)")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    con = hd.ensure_catalog()          # 触发加列迁移（不丢数据）

    # 1) 派生量：一条 SQL，对全部数据集瞬间生效
    store.run(con,
        "UPDATE datasets SET "
        "duration_s = CASE WHEN fps > 0 THEN total_frames / fps ELSE 0 END, "
        "avg_episode_frames = CASE WHEN n_episodes > 0 THEN total_frames * 1.0 / n_episodes ELSE 0 END")
    print("[ok] 派生量(duration_s / avg_episode_frames) 已对全部数据集更新。")

    if args.derived_only:
        store.close(con)
        return

    # 2) HF 规格回填（只补 HF 且尚未补过的）
    rows = store.run(con, "SELECT dataset_id, source, source_format, size_bytes FROM datasets ORDER BY name")
    todo = [r[0] for r in rows if _is_hf(r[1], r[2]) and (args.force or not r[3])]
    if args.limit:
        todo = todo[:args.limit]
    print(f"待联网回填 {len(todo)} 个 HF 数据集…")

    def work(rid):
        try:
            return rid, enrich_hf(rid)
        except Exception as e:
            return rid, {"__err__": repr(e)[:80]}

    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for rid, m in ex.map(work, todo):
            if "__err__" in m:
                print(f"  [skip] {rid}: {m['__err__']}")
                continue
            store.run(con,
                "UPDATE datasets SET size_bytes=?, last_modified=?, downloads=?, likes=?, "
                "video_resolution=?, video_codec=? WHERE dataset_id=?",
                [m["size_bytes"], m["last_modified"], m["downloads"], m["likes"],
                 m["video_resolution"], m["video_codec"], rid])
            ok += 1
            sz = m["size_bytes"] / 1e9
            print(f"  [ok] {rid:<45} {sz:.2f} GB  {m['video_resolution']} {m['video_codec']}")

    print(f"\n完成：{ok}/{len(todo)} 个已回填规格。")
    store.close(con)


if __name__ == "__main__":
    main()
