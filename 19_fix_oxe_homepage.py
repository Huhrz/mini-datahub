"""
修正 OXE 数据集的主页链接
============================

问题：所有 OXE 子数据集的 homepage 都指向同一个总项目页
（robotics-transformer-x.github.io），点进去分不出是哪个数据集；而且该域名
在国内服务器不可达，还会造成链接体检误报。

修正优先级（都指向**该数据集自己的**页面）：
  1) 社区 HF LeRobot 转换版仓库（IPEC-COMMUNITY/xxx_lerobot）—— 有独立说明、文件浏览、可视化
  2) GCS 上它自己的数据目录
  3) 保底：OXE 总项目页

用法（容器内跑；走 compose 配的 HF 镜像）：
    python 19_fix_oxe_homepage.py --dry     # 预览
    python 19_fix_oxe_homepage.py           # 写库
"""

import argparse
from concurrent.futures import ThreadPoolExecutor

import store
import oxe_registry as R


def resolve(name: str):
    """返回 (新主页, 说明)。"""
    repo = R.hf_conversion_guess(name)
    try:
        from huggingface_hub import dataset_info
        dataset_info(repo)
        return f"https://huggingface.co/datasets/{repo}", "HF转换版"
    except Exception:
        pass
    return f"https://storage.googleapis.com/gresearch/robotics/{name}", "GCS数据目录"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只预览不写库")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    con = store.connect(read_only=args.dry and not store.is_pg())
    rows = store.run(con, "SELECT dataset_id, name, homepage FROM datasets "
                          "WHERE source = 'openx' ORDER BY name")
    if not rows:
        print("目录里没有 OXE 数据集。")
        return
    print(f"待修正 {len(rows)} 个 OXE 数据集的主页…\n")

    def work(r):
        did, name, old = r
        new, why = resolve(name)
        return did, name, old, new, why

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(work, rows))

    changed = [(new, did) for did, name, old, new, why in results if new != old]
    for did, name, old, new, why in results:
        mark = "→" if new != old else "="
        print(f"  {mark} {name[:42]:<44} [{why}] {new}")

    print(f"\n将更新 {len(changed)}/{len(rows)} 条。")
    if args.dry:
        print("(dry run，未写库)")
    elif changed:
        store.run_many(con, "UPDATE datasets SET homepage = ? WHERE dataset_id = ?", changed)
        print("[ok] 已写回。")
    store.close(con)


if __name__ == "__main__":
    main()
