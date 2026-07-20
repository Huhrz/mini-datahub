"""
源适配器框架（G1 源适配器 + B3 归一化画像）
=============================================

设计：每种格式 = 一个适配器函数，统一接口、注册即用。
加一种新格式，只需在这里再写一个 @register("xxx") 的函数 —— 不动其它代码。

统一接口：adapter(identifier) -> DatasetMeta
  identifier 对不同源含义不同：HF/OXE 是数据集名，HDF5/MCAP 是本地文件路径。

各适配器把"重型库"（tfds/h5py/mcap）放在函数内部 lazy import，
所以 import sources 本身不需要装齐所有库——你用哪个格式才需要哪个库。
"""

import os
import json
from schema import DatasetMeta, license_fields

# ---------------- 注册表 ----------------
REGISTRY = {}


def register(source_type):
    def deco(fn):
        REGISTRY[source_type] = fn
        return fn
    return deco


def fetch(source_type, identifier) -> DatasetMeta:
    if source_type not in REGISTRY:
        raise ValueError(f"未知格式 '{source_type}'；已注册: {list(REGISTRY)}")
    meta = REGISTRY[source_type](identifier)
    # 接入即打"元数据初筛分"（零下载）；深度质检分(learnability)留给 06 按需补
    try:
        from quality import metadata_quality
        if getattr(meta, "quality_score", -1) is None or meta.quality_score < 0:
            s, rep = metadata_quality(meta)
            meta.quality_score = s
            meta.quality_report = rep
    except Exception:
        pass
    return meta


def available():
    return list(REGISTRY)


import re

# 只在有真实信号时判定 simulation；其余一律 unknown（不假装是 teleop）。
# 采集方式(遥操作/脚本/仿真/自主/人类视频)通常无法从元数据可靠判定，诚实为上。
_SIM_RE = re.compile(
    r"(^|[_\-/ ])(sim|simulation|simulated|mujoco|isaac|isaacgym|genesis|"
    r"pybullet|sapien|gazebo|synthetic)([_\-/ ]|$)")


def _detect_provenance(*hints) -> str:
    blob = " ".join(str(h) for h in hints if h).lower()
    if _SIM_RE.search(blob):
        return "simulation"
    return "unknown"


def _video_specs(feats: dict):
    """从 features 取主相机分辨率(WxH)与视频编码。LeRobot shape 常见 [H,W,C]。"""
    for v in feats.values():
        if v.get("dtype") == "video":
            shp = v.get("shape") or []
            res = f"{int(shp[1])}x{int(shp[0])}" if len(shp) >= 2 else ""
            codec = (v.get("video_info") or {}).get("video.codec", "") or ""
            return res, codec
    return "", ""


def _hf_meta(repo_id: str) -> dict:
    """一次 dataset_info 调用取 license / 总大小 / 更新时间 / 下载 / 点赞。"""
    out = {"license": "unknown", "size_bytes": 0, "last_modified": "", "downloads": 0, "likes": 0}
    try:
        from huggingface_hub import dataset_info
        di = dataset_info(repo_id, files_metadata=True)
        out["license"] = (di.card_data or {}).get("license", "unknown") or "unknown"
        out["last_modified"] = str(getattr(di, "lastModified", "") or "")[:10]
        out["downloads"] = int(getattr(di, "downloads", 0) or 0)
        out["likes"] = int(getattr(di, "likes", 0) or 0)
        total = 0
        for s in (getattr(di, "siblings", None) or []):
            sz = getattr(s, "size", None)
            if sz:
                total += int(sz)
        out["size_bytes"] = total
    except Exception:
        pass
    return out


def _guess_embodiment(robot_type: str) -> str:
    r = (robot_type or "").lower()
    if "aloha" in r or "bimanual" in r or "dual" in r:
        return "bimanual"
    if "humanoid" in r or "h1" in r or "g1" in r or "agibot" in r:
        return "humanoid"
    if "mobile" in r:
        return "mobile"
    return "single_arm"


# ================= 适配器 1：HuggingFace / LeRobot =================
@register("lerobot_hf")
def from_lerobot_hf(repo_id: str) -> DatasetMeta:
    """只拉 meta/info.json + 卡片 license，组装目录项（联邦：不下数据本体）。"""
    from huggingface_hub import hf_hub_download

    info = json.load(open(hf_hub_download(repo_id, "meta/info.json", repo_type="dataset")))
    hf = _hf_meta(repo_id)            # license + 大小 + 更新时间 + 热度（一次调用）
    license_str = hf["license"]

    feats = info.get("features", {})
    cams = [k for k, v in feats.items() if v.get("dtype") in ("video", "image")]
    robot = info.get("robot_type", "")
    spdx, com, redist = license_fields(license_str)
    act_dim = (feats.get("action", {}).get("shape") or [0])[0]
    mods = (["rgb"] if cams else []) + (["state"] if "observation.state" in feats else [])
    if any("language" in k or k == "task" for k in feats):
        mods.append("language")

    # 拉取任务的自然语言描述（给 taxonomy 对齐用）；兼容 v2.1(jsonl) 与 v3.0(parquet)
    tasks = []
    # v2.1: meta/tasks.jsonl
    try:
        tp = hf_hub_download(repo_id, "meta/tasks.jsonl", repo_type="dataset")
        for line in open(tp):
            line = line.strip()
            if line:
                t = json.loads(line).get("task")
                if t:
                    tasks.append(t)
    except Exception:
        pass
    # v3.0: meta/tasks.parquet（用 duckdb 读，免额外依赖）
    if not tasks:
        try:
            tp = hf_hub_download(repo_id, "meta/tasks.parquet", repo_type="dataset")
            import duckdb
            df = duckdb.sql(f"SELECT * FROM read_parquet('{tp}')").df()
            col = "task" if "task" in df.columns else df.select_dtypes(include="object").columns[0]
            tasks = [str(t) for t in df[col].tolist() if t]
        except Exception:
            pass
    tasks = list(dict.fromkeys(tasks))[:50]   # 去重 + 限量

    n_ep = int(info.get("total_episodes", 0))
    n_fr = int(info.get("total_frames", 0))
    fps = float(info.get("fps", 0) or 0)
    res, codec = _video_specs(feats)

    return DatasetMeta(
        dataset_id=repo_id, name=repo_id.split("/")[-1], source="huggingface",
        source_uri=f"https://huggingface.co/datasets/{repo_id}",
        source_format=f"lerobot_{info.get('codebase_version', 'v?')}",
        license_spdx=spdx, commercial_ok=com, redistribute_ok=redist,
        provenance_type=_detect_provenance(repo_id, robot), embodiment=_guess_embodiment(robot), robot_model=robot,
        dof=int(act_dim), modalities=mods, tasks=tasks, fps=fps,
        n_cameras=len(cams), n_episodes=n_ep, total_frames=n_fr,
        duration_s=round(n_fr / fps, 1) if fps else 0.0,
        avg_episode_frames=round(n_fr / n_ep, 1) if n_ep else 0.0,
        video_resolution=res, video_codec=codec,
        size_bytes=hf["size_bytes"], last_modified=hf["last_modified"],
        downloads=hf["downloads"], likes=hf["likes"],
        has_failure_labels=("next.reward" in feats),
        homepage=f"https://huggingface.co/datasets/{repo_id}",
    )


# ================= 适配器 2：Open X-Embodiment / RLDS =================
def _parse_tfds_info(info: dict, name: str, version: str, url: str) -> DatasetMeta:
    """从 TFDS dataset_info.json + OXE 登记表提取【富】目录项，归一化到统一 schema。
    登记表给本体/模态/相机/动作约定（可靠推导）；dataset_info.json 给轨迹数/大小/描述。"""
    import oxe_registry as R

    # 轨迹数 + 大小（来自实时 dataset_info.json）
    n_ep, size = 0, 0
    for sp in info.get("splits", []):
        for s in sp.get("shardLengths", []):
            try:
                n_ep += int(s)
            except Exception:
                pass
        try:
            size += int(sp.get("numBytes", 0) or sp.get("num_bytes", 0) or 0)
        except Exception:
            pass
    if not size:
        try:
            size = int(info.get("downloadSize", 0) or info.get("dataSize", 0) or 0)
        except Exception:
            pass
    blob = json.dumps(info).lower()

    if R.has(name):
        # 有登记表 → 归一化元数据（跨源可比的核心）
        mods = R.modalities(name)
        if ("language_instruction" in blob or "natural_language" in blob) and "language" not in mods:
            mods.append("language")
        emb = R.embodiment(name)
        cams = R.cameras(name)
        conv, dof = R.action_convention(name)
        prov = R.provenance(name)
        n_cam = len(cams)
    else:
        # 未登记 → 从 dataset_info.json 尽力启发式抽取
        mods = []
        if "image" in blob:
            mods.append("rgb")
        if "depth" in blob:
            mods.append("depth")
        if "state" in blob or "proprio" in blob:
            mods.append("state")
        if "language_instruction" in blob or "natural_language" in blob:
            mods.append("language")
        emb, cams, conv, dof, n_cam = "single_arm", [], {}, 0, 0
        prov = _detect_provenance(name, url)

    return DatasetMeta(
        dataset_id=f"oxe/{name}", name=name, source="openx",
        source_uri=url, source_format="rlds", version=version,
        # OXE 各数据集许可不一，无法逐一核实 → 诚实标未知（导出时按 license 门禁拦截）
        license_spdx="unknown", commercial_ok=False, redistribute_ok=False,
        provenance_type=prov, embodiment=emb, dof=dof,
        action_convention=conv, modalities=mods, n_cameras=n_cam,
        n_episodes=n_ep, size_bytes=size,
        homepage="https://robotics-transformer-x.github.io/",
    )


@register("openx_rlds")
def from_openx_rlds(identifier: str) -> DatasetMeta:
    """
    联邦接入 OXE（RLDS）的元数据，只拉几 KB 的 dataset_info.json，不下 tfrecord。
    identifier 可以是：
      - 直接的 dataset_info.json URL
      - 数据集名，如 'fractal20220817_data'（默认猜版本 0.1.0）
      - 'name@version'
    """
    import requests

    if identifier.startswith("http"):
        url, name, version = identifier, identifier.split("/")[-3], identifier.split("/")[-2]
    else:
        name, version = (identifier.split("@") + ["0.1.0"])[:2]
        url = f"https://storage.googleapis.com/gresearch/robotics/{name}/{version}/dataset_info.json"
    info = requests.get(url, timeout=15).json()
    return _parse_tfds_info(info, name, version, url)


# ================= 适配器 3：HDF5（机构自定义） =================
@register("hdf5")
def from_hdf5(path: str) -> DatasetMeta:
    """读本地 .hdf5/.h5 结构，抽取【富】元数据并归一化（相机数/分辨率/状态维/
    动作约定/帧数/时长/大小/本体）。不同实验室布局不一，做稳健启发式。"""
    import h5py
    import numpy as np

    shapes, dtypes = {}, {}

    def visit(name, obj):
        if isinstance(obj, h5py.Dataset):
            shapes[name] = obj.shape
            dtypes[name] = obj.dtype

    fps = 0.0
    with h5py.File(path, "r") as f:
        f.visititems(visit)
        top = list(f.keys())
        demos = []
        if "data" in f and isinstance(f["data"], h5py.Group):
            demos = [k for k in f["data"].keys() if k.startswith(("demo", "episode", "traj"))]
        n_ep = len(demos) or sum(1 for k in top if k.startswith(("demo", "episode", "traj"))) or 1
        for kk in ("fps", "frame_rate", "control_freq"):
            if kk in f.attrs:
                try:
                    fps = float(f.attrs[kk])
                except Exception:
                    pass

    def _is_img(s, dt):
        return (len(s) == 4 and s[-1] in (1, 3)) or (len(s) == 3 and dt == np.uint8 and s[1] >= 16 and s[2] >= 16)

    img_keys = [k for k, s in shapes.items() if _is_img(s, dtypes[k])]
    cam_names = sorted(set(k.split("/")[-1] for k in img_keys))
    n_cam = len(cam_names)
    resolution = ""
    if img_keys:
        s = shapes[img_keys[0]]
        if len(s) >= 3:
            resolution = f"{int(s[2])}x{int(s[1])}"

    dof = state_dim = total_frames = 0
    for k, s in shapes.items():
        leaf = k.split("/")[-1]
        if leaf in ("action", "actions") and len(s) >= 1:
            if not dof:
                dof = int(s[-1])
            total_frames += int(s[0])
        if leaf in ("qpos", "state", "joint_positions", "ee_pose") and len(s) >= 1 and not state_dim:
            state_dim = int(s[-1])

    mods = []
    if img_keys:
        mods.append("rgb")
    if any("depth" in k.lower() for k in shapes):
        mods.append("depth")
    if state_dim or any(k.split("/")[-1] in ("qpos", "state") for k in shapes):
        mods.append("state")

    blob = " ".join(shapes).lower()
    is_bimanual = ("left" in blob and "right" in blob) or dof >= 12 or "bimanual" in blob
    emb = "bimanual" if is_bimanual else "single_arm"
    conv = {"space": "joint"} if any(k.split("/")[-1] in ("qpos", "joint_positions") for k in shapes) else {}

    fid = os.path.basename(path)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return DatasetMeta(
        dataset_id=f"local/{fid}", name=fid, source="institutional",
        source_uri=os.path.abspath(path), source_format="hdf5",
        license_spdx="unknown", commercial_ok=False, redistribute_ok=False,
        provenance_type=_detect_provenance(fid), embodiment=emb,
        dof=dof, action_convention=conv, modalities=mods, n_cameras=n_cam,
        n_episodes=max(n_ep, 1), total_frames=total_frames, fps=fps,
        duration_s=round(total_frames / fps, 1) if fps else 0.0,
        avg_episode_frames=round(total_frames / n_ep, 1) if n_ep else 0.0,
        video_resolution=resolution, size_bytes=size,
        homepage="",
    )


# ================= 适配器 4：rosbag / MCAP（ROS 原生） =================
@register("mcap")
def from_mcap(path: str) -> DatasetMeta:
    """读本地 .mcap 的 summary，抽取【富】元数据：相机数/时长/模态/本体/大小。"""
    from mcap.reader import make_reader

    topics, total_msgs = [], 0
    t0 = t1 = None
    with open(path, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        if summary and summary.statistics:
            st = summary.statistics
            total_msgs = st.message_count
            t0 = getattr(st, "message_start_time", None)
            t1 = getattr(st, "message_end_time", None)
        if summary:
            for ch in summary.channels.values():
                topics.append(ch.topic)

    joined = " ".join(topics).lower()
    img_topics = sorted(set(t for t in topics
                            if ("image" in t.lower() or "camera" in t.lower())
                            and "depth" not in t.lower() and "info" not in t.lower()))
    mods = []
    if img_topics or "image" in joined or "camera" in joined:
        mods.append("rgb")
    if "depth" in joined:
        mods.append("depth")
    if "joint" in joined or "state" in joined:
        mods.append("state")
    if "scan" in joined or "lidar" in joined or "points" in joined:
        mods.append("lidar")

    dur = round((t1 - t0) / 1e9, 1) if (t0 and t1 and t1 > t0) else 0.0
    emb = "bimanual" if ("left" in joined and "right" in joined) else "single_arm"
    fid = os.path.basename(path)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return DatasetMeta(
        dataset_id=f"local/{fid}", name=fid, source="institutional",
        source_uri=os.path.abspath(path), source_format="mcap",
        license_spdx="unknown", commercial_ok=False, redistribute_ok=False,
        provenance_type=_detect_provenance(fid), embodiment=emb,
        modalities=mods, n_cameras=len(img_topics), n_episodes=1,
        total_frames=total_msgs, duration_s=dur, size_bytes=size,
        homepage="",
    )
