"""
合成示例数据生成器 —— 让你"不用下载任何东西"就能先把整条线跑通看效果。

它伪造一条机器人轨迹：
  - 一个 2 自由度机械臂的关节角随时间做正弦摆动（state / action）
  - 一张 256x256 的图，里面一个彩色方块跟着"末端"移动（模拟摄像头画面）
真实接入 LeRobot 数据集后，把这里换成 LeRobotDataset 即可，下游代码不用改。
"""

import numpy as np


def make_demo_episode(dof: int = 7, length: int = 120, fps: float = 30.0,
                      seed: int = 0, task_text: str = "demo replay"):
    """
    按指定自由度生成一条合成轨迹（给网页"点数据集→回放"用）。
    每个关节一条不同相位的正弦曲线 + 一张方块跟随移动的摄像头画面。
    真实接入时，把这里换成对应数据集的真实 episode 即可，下游 viz 不变。
    """
    dof = max(1, int(dof))
    t = np.linspace(0, 2 * np.pi, length)
    state = np.stack(
        [0.7 * np.sin(t + j * 0.6) for j in range(dof)], axis=1
    ).astype(np.float32)
    action = np.diff(state, axis=0, prepend=state[:1]).astype(np.float32)

    cx = (0.5 + 0.35 * np.cos(state[:, 0])) * 256
    cy = (0.5 + 0.35 * np.sin(state[:, min(1, dof - 1)])) * 256
    frames = []
    for i in range(length):
        img = np.full((256, 256, 3), 30, dtype=np.uint8)
        x, y = int(cx[i]), int(cy[i])
        img[max(0, y - 10):y + 10, max(0, x - 10):x + 10] = (230, 80, 80)
        frames.append(img)

    return {
        "images": np.stack(frames),
        "state": state,
        "action": action,
        "fps": float(fps),
        "task_text": task_text,
    }


def make_synthetic_episode(length: int = 120, seed: int = 0):
    """返回一条合成轨迹的逐帧数据。"""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, length)

    # 2 自由度关节角度（state），动作 = 下一帧角度的增量
    j1 = 0.8 * np.sin(t)
    j2 = 0.5 * np.sin(2 * t + 0.5)
    state = np.stack([j1, j2], axis=1).astype(np.float32)          # (L, 2)
    action = np.diff(state, axis=0, prepend=state[:1]).astype(np.float32)

    # 末端在画面里的位置（由关节角简单映射）
    cx = (0.5 + 0.35 * np.cos(j1)) * 256
    cy = (0.5 + 0.35 * np.sin(j2)) * 256

    frames = []
    for i in range(length):
        img = np.full((256, 256, 3), 30, dtype=np.uint8)  # 深灰背景
        x, y = int(cx[i]), int(cy[i])
        # 画一个 20x20 的彩色方块当作"被操作物体/末端"
        x0, y0 = max(0, x - 10), max(0, y - 10)
        x1, y1 = min(256, x + 10), min(256, y + 10)
        img[y0:y1, x0:x1] = (230, 80, 80)  # 红色方块
        frames.append(img)

    return {
        "images": np.stack(frames),   # (L, 256, 256, 3)
        "state": state,               # (L, 2)
        "action": action,             # (L, 2)
        "task_text": "move the red block along a looping path",
        "fps": 30.0,
    }
