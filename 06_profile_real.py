"""
步骤 4.5：对【真实】数据集采样质检并写回目录（本地运行）
=========================================================

把第 1、2 条扩展落地：
  - 第 1 条：从真实 LeRobotDataset 抽取若干轨迹 → 走同一套质检引擎 → 写回 schema。
  - 第 2 条：RLDS/OpenX 数据先用官方工具转成 LeRobot 格式，再用本脚本质检入库
            （转换命令见下方注释），因为转换后就是 LeRobot 格式，复用同一条链路。

需要本地联网 + `pip install lerobot`。

用法：
    python 06_profile_real.py lerobot/pusht --episodes 5

把 RLDS 数据接进来（先转换，再质检）：
    # 1) 安装并运行官方转换（把 OpenX/RLDS 转成 LeRobot 格式）
    #    pip install lerobot
    #    python -m lerobot.datasets.port_datasets.openx_rlds  <参数见其文档>
    #    或社区工具 forge：https://github.com/arpitg1304/forge
    # 2) 转换产物是 LeRobot 数据集，直接：
    #    python 06_profile_real.py <你的本地/HF 数据集 id>
"""

import sys
import argparse
import numpy as np

import hub_data as hd
from quality import compute_quality, aggregate_dataset_quality


def load_canonical_episodes(repo_id, n_episodes=5):
    """从真实 LeRobotDataset 取前 n 条轨迹，转成 canonical 形式（给质检用）。"""
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(repo_id)
    n = min(n_episodes, ds.num_episodes)
    canons = []
    for ep in range(n):
        frm = ds.episode_data_index["from"][ep].item()
        to = ds.episode_data_index["to"][ep].item()
        states, actions = [], []
        for idx in range(frm, to):
            s = ds[idx]
            states.append(np.asarray(s["observation.state"]))
            actions.append(np.asarray(s["action"]))
        canons.append({
            "images": None,                      # 质检只需 state/action，省内存不取图
            "state": np.stack(states),
            "action": np.stack(actions),
            "fps": ds.fps,
        })
    return canons, ds.num_episodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_id")
    ap.add_argument("--episodes", type=int, default=5, help="采样质检的轨迹数")
    args = ap.parse_args()

    print(f"[info] 加载真实数据集 {args.repo_id} 的前 {args.episodes} 条轨迹做质检…")
    canons, total = load_canonical_episodes(args.repo_id, args.episodes)

    print(f"\n逐条质检（采样 {len(canons)}/{total} 条）：")
    for i, c in enumerate(canons):
        r = compute_quality(c)
        print(f"  ep{i}: 质量分={r['quality_score']} 可学性={r['learnability_score']} {r['report']}")

    agg = aggregate_dataset_quality(canons)
    print(f"\n数据集级聚合分：质量={agg['quality_score']} 可学性={agg['learnability_score']}")

    # 写回目录（若该数据集还没登记，先用 03 接入元数据；这里只更新分数）
    con = hd.ensure_catalog()
    updated = con.execute(
        "UPDATE datasets SET quality_score=?, learnability_score=? WHERE dataset_id=?",
        [agg["quality_score"], agg["learnability_score"], args.repo_id],
    )
    n = con.execute("SELECT COUNT(*) FROM datasets WHERE dataset_id=?", [args.repo_id]).fetchone()[0]
    if n == 0:
        print(f"\n[提示] 目录里还没有 {args.repo_id}，请先运行："
              f"\n        python 03_ingest_real_lerobot.py {args.repo_id}\n      再跑本脚本写回分数。")
    else:
        print(f"\n[ok] 已把质检分写回 {args.repo_id}（刷新网页可见）。")
    con.close()


if __name__ == "__main__":
    main()
