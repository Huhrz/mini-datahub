"""
批量预缓存数据集截图（缓存暖机）—— 全格式覆盖
================================================

对目录里的数据集，用 ffmpeg 从视频抽几帧存成本地 JPEG，
让画廊"按图浏览"秒开、不再每次去 HF 拉视频。存储极小（每集几十~上百 KB）。

覆盖范围：
  - **LeRobot / HF**：直接从其视频抽帧。
  - **OXE / RLDS**：原始 tfrecord 不便抽帧 → 自动映射到社区 HF LeRobot 转换版
    （IPEC-COMMUNITY/xxx_lerobot），从转换版抽帧，缓存挂在 OXE 条目下。
  - 其它（本地 HDF5 等）：跳过。

用法（容器内跑；走 compose 里配的 HF 镜像）：
    python 18_cache_thumbs.py                 # 全部（跳过已缓存）
    python 18_cache_thumbs.py --limit 50      # 先缓存 50 个
    python 18_cache_thumbs.py --force         # 重抽（覆盖已缓存）
    python 18_cache_thumbs.py --only-oxe      # 只补 OXE
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import store
import thumbs
import episode


def _hf_video_url(repo_id):
    """从一个 HF LeRobot 仓库取首个视频 URL。"""
    try:
        info = episode._info(repo_id)
        return episode._first_video_url(repo_id, info)
    except Exception:
        return None


def _resolve(dataset_id, source, fmt):
    """返回 (取帧用的 repo, 说明)。取不到返回 (None, 原因)。"""
    if source == "huggingface" or "lerobot" in str(fmt or ""):
        return dataset_id, "HF"
    if source == "openx":
        # OXE → 社区 HF LeRobot 转换版
        try:
            import oxe_registry as R
            guess = R.hf_conversion_guess(dataset_id.split("/")[-1])
            if _hf_video_url(guess):
                return guess, "OXE→" + guess
            return None, "无 HF 转换版"
        except Exception as e:
            return None, f"映射失败 {type(e).__name__}"
    return None, f"格式暂不支持({fmt})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="重抽已缓存的")
    ap.add_argument("--only-oxe", action="store_true", help="只处理 OXE 数据集")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    con = store.connect(read_only=not store.is_pg())
    rows = store.run(con, "SELECT dataset_id, source, source_format FROM datasets ORDER BY name")
    store.close(con)

    todo = []
    for did, src, fmt in rows:
        if args.only_oxe and src != "openx":
            continue
        if not args.force and thumbs.has_cache(did):
            continue
        todo.append((did, src, fmt))
    if args.limit:
        todo = todo[:args.limit]

    total_all = len(rows)
    cached_before = sum(1 for r in rows if thumbs.has_cache(r[0]))
    print(f"目录共 {total_all} 个数据集，已有缓存 {cached_before} 个，本轮处理 {len(todo)} 个…\n")

    def work(item):
        did, src, fmt = item
        repo, why = _resolve(did, src, fmt)
        if not repo:
            return did, 0, why
        url = _hf_video_url(repo)
        if not url:
            return did, 0, "取不到视频地址"
        return did, thumbs.extract(did, url), why

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for did, n, why in ex.map(work, todo):
            if n > 0:
                ok += 1
                print(f"  [ok]   {did:<46} {n} 张   ({why})")
            else:
                fail += 1
                print(f"  [skip] {did:<46} {why}")

    after = sum(1 for r in rows if thumbs.has_cache(r[0]))
    print(f"\n本轮成功 {ok}，跳过 {fail}。")
    print(f"目录总覆盖率：{after}/{total_all} = {round(100*after/max(total_all,1))}%")


if __name__ == "__main__":
    main()
