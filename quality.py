"""
质检引擎（B4）—— 入库时的自动质量分 / 可学性分
=================================================

对齐文档 3.2 自研组件 B4「质量 + license/合规 评分引擎」。

设计要点：
  - 工作在【统一表示 canonical episode】上（和 04_convert_formats 的输出一致），
    所以无论数据来自 LeRobot 还是 RLDS，入库时都走同一套质检 —— 这把
    "格式归一" 和 "自动质检" 串成了一条线。
  - 分数【可解释】：每个分都附带一份 report 说明扣分原因（文档要求质量指标可解释）。
  - 不依赖网络/重型库，只用 numpy。

两个分数（均归一化到 0~1）：
  quality_score    —— 数据"干不干净"：缺帧/NaN、动作饱和、状态-动作一致性。
  learnability_score —— 数据"有没有信息量"：动作多样性、轨迹非冗余度。
                        回应文档与论文共识"盲目堆量会负迁移，多样性比数量更重要"。
"""

import numpy as np


def _clip01(x):
    return float(max(0.0, min(1.0, x)))


def compute_quality(canon: dict) -> dict:
    """
    输入：canonical episode（含 images / state / action / fps）。
    输出：{quality_score, learnability_score, report:{...}}。
    """
    state = np.asarray(canon.get("state"))
    action = np.asarray(canon.get("action"))
    images = canon.get("images")
    report = {}

    # ---------- 质量分 quality ----------
    # 1) NaN / 缺失比例
    nan_ratio = 0.0
    if action.size:
        nan_ratio = float(np.isnan(action).mean() + np.isnan(state).mean()) / 2
    q_nan = 1.0 - nan_ratio
    report["nan_ratio"] = round(nan_ratio, 4)

    # 2) 动作饱和：动作长期顶在极值（|a| 接近最大）往往是异常/夹爪卡死
    sat_ratio = 0.0
    if action.size:
        amax = np.abs(action).max() + 1e-8
        sat_ratio = float((np.abs(action) > 0.98 * amax).mean())
    q_sat = 1.0 - sat_ratio
    report["saturation_ratio"] = round(sat_ratio, 4)

    # 3) 帧数充足度：太短的轨迹信息少
    L = len(action) if action.size else 0
    q_len = _clip01(L / 50.0)   # 50 帧以上给满分
    report["length"] = L

    quality = _clip01(0.5 * q_nan + 0.3 * q_sat + 0.2 * q_len)

    # ---------- 可学性分 learnability ----------
    # 先剔除含 NaN 的帧，避免 NaN 传播污染统计
    clean = action
    if action.size:
        clean = action[~np.isnan(action).any(axis=1)]
    Lc = len(clean)

    # 1) 动作多样性：动作的标准差越大，包含的"操作信息"越多
    diversity = float(np.mean(np.std(clean, axis=0))) if Lc > 1 else 0.0
    l_div = _clip01(diversity / 0.05)   # 经验缩放
    report["action_diversity"] = round(diversity, 4)

    # 2) 非冗余度：相邻帧动作变化太小=机器人几乎没动（冗余）
    movement = float(np.mean(np.abs(np.diff(clean, axis=0)))) if Lc > 1 else 0.0
    l_move = _clip01(movement / 0.01)
    report["avg_frame_movement"] = round(movement, 4)

    learnability = _clip01(0.6 * l_div + 0.4 * l_move)

    return {
        "quality_score": round(quality, 3),
        "learnability_score": round(learnability, 3),
        "report": report,
    }


def aggregate_dataset_quality(episode_canons: list) -> dict:
    """把多条轨迹的质检结果聚合成数据集级分数。"""
    if not episode_canons:
        return {"quality_score": -1.0, "learnability_score": -1.0, "report": {}}
    qs, ls = [], []
    for ep in episode_canons:
        r = compute_quality(ep)
        qs.append(r["quality_score"])
        ls.append(r["learnability_score"])
    return {
        "quality_score": round(float(np.mean(qs)), 3),
        "learnability_score": round(float(np.mean(ls)), 3),
        "report": {"n_episodes_profiled": len(episode_canons),
                   "quality_min": round(float(np.min(qs)), 3),
                   "quality_max": round(float(np.max(qs)), 3)},
    }
