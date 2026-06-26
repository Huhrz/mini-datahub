"""
步骤 3：格式归一 / 粘合层 demo（DataHub 的核心价值）
=====================================================

不同来源的数据"长得完全不一样"：
  - LeRobot 式：字段叫 observation.state / action，fps=30
  - RLDS 式（OpenX）：嵌套在 steps 里，字段叫 observation.image / action，
                      控制频率叫 control_frequency=5，语言指令叫 language_instruction

"粘合层"要做的，就是用一张【适配器映射表】，把它们都翻译成**同一种规范表示**
(CanonicalEpisode)，下游的可视化、入库、训练就再也不用关心源格式了。

这正是真实项目里 openx2lerobot / forge 这些转换工具在做的事 —— 这里用合成数据
把"映射"这件事的本质演示出来，不依赖网络、可直接运行：

    python 04_convert_formats.py
"""

import numpy as np
from demo import make_synthetic_episode
from schema import EpisodeMeta


# ---------- 规范表示：所有格式都翻译成它 ----------
def canonical(images, state, action, fps, task_text):
    return {
        "images": np.asarray(images),
        "state": np.asarray(state, dtype=np.float32),
        "action": np.asarray(action, dtype=np.float32),
        "fps": float(fps),
        "task_text": task_text,
    }


# ---------- 适配器 1：LeRobot 式 → 规范 ----------
def from_lerobot(raw: dict):
    """raw 已经接近规范，直接映射字段。"""
    return canonical(
        images=raw["images"],
        state=raw["state"],
        action=raw["action"],
        fps=raw["fps"],
        task_text=raw["task_text"],
    )


# ---------- 适配器 2：RLDS(OpenX) 式 → 规范 ----------
def from_rlds(raw: dict):
    """
    RLDS 式数据是"按 step 嵌套"的，字段命名也不同。这里演示真实会遇到的差异：
      - 数据在 raw['steps'] 列表里，每个 step 一帧
      - 图像键 observation/image，状态键 observation/state，动作键 action
      - 频率叫 control_frequency，语言指令叫 language_instruction
    """
    steps = raw["steps"]
    images = np.stack([s["observation"]["image"] for s in steps])
    state = np.stack([s["observation"]["state"] for s in steps])
    action = np.stack([s["action"] for s in steps])
    meta = raw.get("metadata", {})
    return canonical(
        images=images,
        state=state,
        action=action,
        fps=meta.get("control_frequency", 10),       # ← 字段名不同
        task_text=meta.get("language_instruction", ""),  # ← 字段名不同
    )


# 适配器注册表：源格式 -> 转换函数（要支持新格式，加一行即可）
ADAPTERS = {
    "lerobot": from_lerobot,
    "rlds": from_rlds,
}


def normalize(source_format: str, raw: dict):
    """统一入口：把任意源格式翻译成规范表示。"""
    if source_format not in ADAPTERS:
        raise ValueError(f"还没有 {source_format} 的适配器，请在 ADAPTERS 里加一个")
    return ADAPTERS[source_format](raw)


def to_episode_meta(canon: dict, dataset_id: str, idx: int, embodiment: str):
    """从规范表示抽取轨迹级元数据（接回 schema / DuckDB）。"""
    L = len(canon["images"])
    return EpisodeMeta(
        episode_uid=f"{dataset_id}#{idx}", dataset_id=dataset_id, episode_index=idx,
        length=L, duration_s=L / canon["fps"], task_text=canon["task_text"],
        embodiment=embodiment, success=None,
        action_dim=canon["action"].shape[1], state_dim=canon["state"].shape[1],
    )


# ---------- 造一个"RLDS 式"的合成轨迹，证明适配器能吃下异构格式 ----------
def make_fake_rlds_episode():
    ep = make_synthetic_episode(length=80, seed=7)
    # 故意改成 RLDS 的嵌套结构 + 不同字段名 + 不同频率
    steps = []
    for i in range(len(ep["images"])):
        steps.append({
            "observation": {"image": ep["images"][i], "state": ep["state"][i]},
            "action": ep["action"][i],
        })
    return {
        "steps": steps,
        "metadata": {"control_frequency": 5, "language_instruction": "pick up the red block (rlds-style)"},
    }


def main():
    print("把两种完全不同结构的源数据，归一成同一种规范表示：\n")

    # 源 A：LeRobot 式
    raw_a = make_synthetic_episode(length=120, seed=0)
    canon_a = normalize("lerobot", raw_a)

    # 源 B：RLDS 式（嵌套结构、字段名/频率都不同）
    raw_b = make_fake_rlds_episode()
    canon_b = normalize("rlds", raw_b)

    for name, canon in [("源A (lerobot式)", canon_a), ("源B (rlds式)", canon_b)]:
        print(f"{name}: images={canon['images'].shape} state={canon['state'].shape} "
              f"action={canon['action'].shape} fps={canon['fps']} task='{canon['task_text']}'")

    print("\n关键点：归一后两者结构完全一致，下游(可视化/入库/训练)无需再区分源格式。")
    print("要支持一种新格式，只需在 ADAPTERS 里加一个适配器函数 —— 这就是'粘合层'。\n")

    # 抽取统一元数据（接回 schema）
    m_a = to_episode_meta(canon_a, "demo/lerobot_src", 0, "single_arm")
    m_b = to_episode_meta(canon_b, "demo/rlds_src", 0, "single_arm")
    print("统一后的轨迹元数据：")
    print(" ", m_a.to_row())
    print(" ", m_b.to_row())


if __name__ == "__main__":
    main()
