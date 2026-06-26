"""
步骤 1：加载一条轨迹并用 Rerun 可视化
======================================

两种模式：
  A) 合成 demo（默认，不用下载）：
        python 01_explore_and_visualize.py
  B) 真实 LeRobot 数据集（需要 pip install lerobot 且能联网）：
        python 01_explore_and_visualize.py --repo-id lerobot/aloha_sim_insertion_human --episode 0

可视化会推流到 Rerun viewer：
  - 左边一路摄像头画面随时间播放
  - 关节 state / action 各维度画成曲线
这正是 hub 里"借书前先翻一翻"的预览能力（底层就是 Rerun）。
"""

import argparse
import numpy as np


def log_to_rerun(images, state, action, fps, task_text, title="mini_datahub_episode"):
    """把逐帧数据推进 Rerun。images:(L,H,W,3) state/action:(L,D)"""
    import rerun as rr

    # 兼容：rerun 0.23+ 把 Scalar 改名为 Scalars
    Scalar = getattr(rr, "Scalars", None) or rr.Scalar

    def set_frame_time(i):
        """兼容新旧 Rerun 的时间轴 API。"""
        if hasattr(rr, "set_time"):           # 新版 (>=0.23)
            try:
                rr.set_time("frame", sequence=i)
                rr.set_time("time", duration=i / fps)
                return
            except Exception:
                pass
        rr.set_time_sequence("frame", i)      # 老版
        rr.set_time_seconds("time", i / fps)

    rr.init(title, spawn=True)   # spawn=True 会自动打开 viewer 窗口
    rr.log("task", rr.TextDocument(task_text), static=True)

    L = len(images)
    for i in range(L):
        set_frame_time(i)
        rr.log("camera/top", rr.Image(images[i]))
        for d in range(state.shape[1]):
            rr.log(f"state/joint_{d}", Scalar(float(state[i, d])))
        for d in range(action.shape[1]):
            rr.log(f"action/joint_{d}", Scalar(float(action[i, d])))
    print(f"[ok] 已推送 {L} 帧到 Rerun viewer。")


def load_real_lerobot(repo_id, episode):
    """从 HuggingFace 加载真实 LeRobot 数据集中的一条轨迹。"""
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

    ds = LeRobotDataset(repo_id)
    print(f"[info] {repo_id}: {ds.num_episodes} episodes, fps={ds.fps}")
    print(f"[info] features: {list(ds.features)}")

    frm = ds.episode_data_index["from"][episode].item()
    to = ds.episode_data_index["to"][episode].item()

    imgs, states, actions = [], [], []
    # 找到第一个图像键、state 键、action 键
    img_key = next((k for k in ds.features if "image" in k), None)
    for idx in range(frm, to):
        s = ds[idx]
        if img_key is not None:
            im = s[img_key]
            im = (im.permute(1, 2, 0).numpy() * 255).astype(np.uint8) if im.ndim == 3 else im.numpy()
            imgs.append(im)
        states.append(s["observation.state"].numpy())
        actions.append(s["action"].numpy())

    images = np.stack(imgs) if imgs else np.zeros((len(states), 64, 64, 3), np.uint8)
    return images, np.stack(states), np.stack(actions), ds.fps, f"{repo_id} ep{episode}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-id", default=None, help="真实 LeRobot 数据集 id；不填则用合成 demo")
    ap.add_argument("--episode", type=int, default=0)
    args = ap.parse_args()

    if args.repo_id:
        images, state, action, fps, task = load_real_lerobot(args.repo_id, args.episode)
    else:
        from demo import make_synthetic_episode
        ep = make_synthetic_episode()
        images, state, action = ep["images"], ep["state"], ep["action"]
        fps, task = ep["fps"], ep["task_text"]
        print("[info] 使用合成 demo 数据（不联网）。要看真实数据集请加 --repo-id。")

    log_to_rerun(images, state, action, fps, task)


if __name__ == "__main__":
    main()
