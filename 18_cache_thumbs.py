"""
批量预缓存数据集截图（缓存暖机）
==================================

对目录里的 LeRobot/HF 数据集，用 ffmpeg 从视频抽几帧存成本地 JPEG，
让画廊"按图浏览"秒开、不再每次去 HF 拉视频。存储极小（每集几十~上百 KB）。

用法（容器内跑；走 compose 里配的 HF 镜像）：
    python 18_cache_thumbs.py                 # 缓存全部（跳过已缓存）
    python 18_cache_thumbs.py --limit 50      # 先缓存 50 个
    python 18_cache_thumbs.py --force         # 重抽（覆盖已缓存）
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import store
import thumbs
import episode


def _video_url(dataset_id):
    try:
        info = episode._info(dataset_id)
        return episode._first_video_url(dataset_id, info)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="重抽已缓存的")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    con = store.connect(read_only=not store.is_pg())
    rows = store.run(con, "SELECT dataset_id, source, source_format FROM datasets ORDER BY name")
    store.close(con)

    def is_lerobot(src, fmt):
        return src == "huggingface" or "lerobot" in str(fmt or "")

    todo = [r[0] for r in rows if is_lerobot(r[1], r[2])
            and (args.force or not thumbs.has_cache(r[0]))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"待缓存 {len(todo)} 个数据集的截图…")

    def work(did):
        url = _video_url(did)
        if not url:
            return did, 0
        return did, thumbs.extract(did, url)

    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for did, n in ex.map(work, todo):
            if n > 0:
                ok += 1
                print(f"  [ok] {did:<48} {n} 张")
            else:
                print(f"  [skip] {did}: 抽帧失败/无视频")

    print(f"\n完成：{ok}/{len(todo)} 个已缓存截图。")


if __name__ == "__main__":
    main()
