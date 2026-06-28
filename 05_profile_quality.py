"""
步骤 4：入库时自动质检（B4 演示）
==================================

演示"数据进门时自动打质量分 / 可学性分"，并把分数写回目录。
用合成数据造三种轨迹，证明质检引擎能区分好坏：
  - good ：动作丰富、干净        → 高分
  - lazy ：机器人几乎没动（冗余） → 可学性低
  - dirty：含 NaN、动作饱和卡死   → 质量低

运行（不联网）：
    python 05_profile_quality.py
"""

import numpy as np
from quality import compute_quality, aggregate_dataset_quality
from demo import make_synthetic_episode
import hub_data as hd


def make_lazy_episode():
    ep = make_synthetic_episode(length=120, seed=1)
    ep["state"][:] = ep["state"][0]          # 状态几乎不变
    ep["action"][:] = ep["action"] * 0.01    # 动作极小：机器人几乎没动
    return ep


def make_dirty_episode():
    ep = make_synthetic_episode(length=30, seed=2)
    ep["action"][5:10] = np.nan              # 缺失帧
    ep["action"][15:] = ep["action"].max()   # 动作长期顶在极值（卡死）
    return ep


def to_canon(ep):
    return {"images": ep["images"], "state": ep["state"],
            "action": ep["action"], "fps": ep["fps"]}


def main():
    cases = {
        "good ": to_canon(make_synthetic_episode(length=120, seed=0)),
        "lazy ": to_canon(make_lazy_episode()),
        "dirty": to_canon(make_dirty_episode()),
    }

    print("逐条轨迹自动质检：\n")
    print(f"{'轨迹':<7}{'质量分':>8}{'可学性':>8}   明细")
    for name, canon in cases.items():
        r = compute_quality(canon)
        print(f"{name:<7}{r['quality_score']:>8}{r['learnability_score']:>8}   {r['report']}")

    print("\n聚合成数据集级分数（把好/差轨迹混在一起）：")
    agg = aggregate_dataset_quality(list(cases.values()))
    print(" ", agg)

    print("\n关键点：质量分能揪出脏数据(dirty)，可学性分能揪出'没信息量'的冗余数据(lazy)。")
    print("这正是文档说的'盲目堆量会负迁移'——入库时就该自动筛，而不是全收。\n")

    # ---------- 把分数写回目录，让网页能显示 ----------
    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("\n[提示] 数据库被占用：请先在跑 streamlit 的终端按 Ctrl+C 关闭网页，"
                  "再运行本脚本写回分数。（DuckDB 同一时间只允许一个程序写）")
            return
        raise
    # 用三种轨迹的分数，给样例库里几个数据集打上演示性分数
    good = compute_quality(cases["good "])
    lazy = compute_quality(cases["lazy "])
    updates = {
        "lerobot/pusht": good,
        "x-humanoid/RoboMIND": good,
        "google/rt_1": lazy,    # 假设这个数据集偏冗余，演示低可学性
    }
    for did, r in updates.items():
        con.execute(
            "UPDATE datasets SET quality_score=?, learnability_score=? WHERE dataset_id=?",
            [r["quality_score"], r["learnability_score"], did],
        )
    print("已把质检分写回 catalog.duckdb（刷新网页可见 quality_score / learnability_score）。")
    print(con.execute(
        "SELECT name, quality_score, learnability_score FROM datasets "
        "WHERE quality_score >= 0 ORDER BY quality_score DESC"
    ).df().to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
