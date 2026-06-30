"""
共享可视化模块 —— 用 Rerun 把【多个不同源的数据集】放进同一个回放器
=====================================================================

这是你那个"无人区"生态位的核心：跨源 + 统一回放。
不同来源（HF/lerobot、OpenX/rlds、机构 hdf5…）先各自经适配器归一成
canonical episode，再统一喂进同一个 Rerun viewer —— 在一个界面里就能
逐个点开、同步回放，而不必关心它们原来是什么格式。

兼容新旧 Rerun：自动适配 set_time / Scalars 的 API 变化。
"""


def _rr_compat(rr):
    """返回 (Scalar 构造器, set_time(i,fps) 函数)，屏蔽新旧版本差异。"""
    Scalar = getattr(rr, "Scalars", None) or rr.Scalar

    def set_time(i, fps):
        if hasattr(rr, "set_time"):                  # 新版 (>=0.23)
            try:
                rr.set_time("frame", sequence=i)
                rr.set_time("time", duration=i / fps)
                return
            except Exception:
                pass
        rr.set_time_sequence("frame", i)             # 老版
        rr.set_time_seconds("time", i / fps)

    return Scalar, set_time


def log_unified(datasets, title="mini_datahub_unified_replay"):
    """
    datasets: list，每项 = {
        "name": 显示名,
        "source_format": 源格式（仅用于标注，证明它们来自不同源）,
        "canon": {"images", "state", "action", "fps", "task_text"}  统一表示
    }
    所有数据集 log 到同一个 Rerun recording，各占一个 entity 路径，
    左侧 Streams 里能分别展开、在一个时间轴上回放。
    """
    import rerun as rr
    Scalar, set_time = _rr_compat(rr)

    rr.init(title, spawn=True)

    # 每个数据集一段说明（标明源格式，凸显"跨源")
    for d in datasets:
        ns = d["name"]
        canon = d["canon"]
        # Rerun 文本框无中文字体，用英文避免显示成方块
        rr.log(f"{ns}/info",
               rr.TextDocument(f"source_format: {d['source_format']}  |  task: {canon.get('task_text', '')}"),
               static=True)

    # 共享时间轴回放（按帧索引对齐；不同 fps 也能同看）
    max_len = max(len(d["canon"]["action"]) for d in datasets)
    for i in range(max_len):
        set_time(i, 30)
        for d in datasets:
            canon = d["canon"]
            ns = d["name"]
            action = canon["action"]
            if i >= len(action):
                continue
            imgs = canon.get("images")
            if imgs is not None:
                rr.log(f"{ns}/camera", rr.Image(imgs[i]))
            for k in range(action.shape[1]):
                rr.log(f"{ns}/action/joint_{k}", Scalar(float(action[i, k])))

    print(f"[ok] 已把 {len(datasets)} 个不同源的数据集推进同一个 Rerun 回放器。")
