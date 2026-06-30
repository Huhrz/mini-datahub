"""
步骤 6：跨源统一回放 demo（你那个"无人区"生态位的核心证明）
=============================================================

把两个【结构完全不同的源格式】的数据集，先各自经适配器归一，再放进
【同一个 Rerun 回放器】——在一个界面里就能逐个点开、同步回放。

这正是 Festivus（只索引、不可视化）和 Humaid（可视化、但只有自家数据）
都没占的位置：跨源 + 统一回放。

运行（不联网，用合成数据代表两个真实源；同一套管道也适用于真实数据）：
    python 08_unified_replay.py

真实数据怎么接：把下面的合成 canon 换成
  - HF/lerobot 源：用 01 的 load_real_lerobot(repo_id) 得到 images/state/action
  - OpenX/rlds 源：用 04 的 from_rlds 适配器（或先 openx2lerobot 转换）
下游 viz.log_unified 完全不用改 —— 这就是"统一回放"的意义。
"""

import importlib.util
from demo import make_synthetic_episode
import viz


def _load(fname, name):
    """加载以数字开头、不能直接 import 的脚本模块。"""
    spec = importlib.util.spec_from_file_location(name, fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    conv = _load("04_convert_formats.py", "conv")   # 复用 04 的归一化适配器

    # 源 A：HuggingFace / LeRobot 格式（平铺字段）
    raw_a = make_synthetic_episode(length=120, seed=0)
    canon_a = conv.normalize("lerobot", raw_a)

    # 源 B：OpenX / RLDS 格式（嵌套 steps、字段名/频率都不同）
    raw_b = conv.make_fake_rlds_episode()
    canon_b = conv.normalize("rlds", raw_b)

    datasets = [
        {"name": "PushT__HF_lerobot", "source_format": "lerobot_v3", "canon": canon_a},
        {"name": "RT1__OpenX_rlds", "source_format": "rlds", "canon": canon_b},
    ]

    print("两个不同源格式的数据集：")
    for d in datasets:
        c = d["canon"]
        print(f"  - {d['name']:<22} 源格式={d['source_format']:<11} "
              f"帧数={len(c['action'])} fps={c['fps']}")
    print("归一后推进同一个 Rerun 回放器（左侧 Streams 可分别展开两个源）…\n")

    viz.log_unified(datasets)


if __name__ == "__main__":
    main()
