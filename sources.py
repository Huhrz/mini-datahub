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
    return REGISTRY[source_type](identifier)


def available():
    return list(REGISTRY)


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
    from huggingface_hub import hf_hub_download, dataset_info

    info = json.load(open(hf_hub_download(repo_id, "meta/info.json", repo_type="dataset")))
    license_str = "unknown"
    try:
        license_str = (dataset_info(repo_id).card_data or {}).get("license", "unknown") or "unknown"
    except Exception:
        pass

    feats = info.get("features", {})
    cams = [k for k, v in feats.items() if v.get("dtype") in ("video", "image")]
    robot = info.get("robot_type", "")
    spdx, com, redist = license_fields(license_str)
    act_dim = (feats.get("action", {}).get("shape") or [0])[0]
    mods = (["rgb"] if cams else []) + (["state"] if "observation.state" in feats else [])

    return DatasetMeta(
        dataset_id=repo_id, name=repo_id.split("/")[-1], source="huggingface",
        source_uri=f"https://huggingface.co/datasets/{repo_id}",
        source_format=f"lerobot_{info.get('codebase_version', 'v?')}",
        license_spdx=spdx, commercial_ok=com, redistribute_ok=redist,
        provenance_type="teleop", embodiment=_guess_embodiment(robot), robot_model=robot,
        dof=int(act_dim), modalities=mods, fps=float(info.get("fps", 0) or 0),
        n_cameras=len(cams), n_episodes=int(info.get("total_episodes", 0)),
        total_frames=int(info.get("total_frames", 0)),
        has_failure_labels=("next.reward" in feats),
        homepage=f"https://huggingface.co/datasets/{repo_id}",
    )


# ================= 适配器 2：Open X-Embodiment / RLDS =================
def _parse_tfds_info(info: dict, name: str, version: str, url: str) -> DatasetMeta:
    """从 TFDS dataset_info.json 提取目录项。OXE 里每个 example = 一条轨迹。"""
    n_ep = 0
    for sp in info.get("splits", []):
        for s in sp.get("shardLengths", []):
            try:
                n_ep += int(s)
            except Exception:
                pass
    blob = json.dumps(info).lower()
    mods = []
    if "image" in blob:
        mods.append("rgb")
    if "natural_language" in blob or "language_instruction" in blob:
        mods.append("language")
    if "state" in blob:
        mods.append("state")
    return DatasetMeta(
        dataset_id=f"oxe/{name}", name=name, source="openx",
        source_uri=url, source_format="rlds",
        license_spdx="apache-2.0", commercial_ok=True, redistribute_ok=True,
        provenance_type="teleop", embodiment="single_arm",
        modalities=mods, n_episodes=n_ep, version=version,
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
    """读本地 .hdf5/.h5 文件结构，尽力提取元数据（不同实验室布局不一，做启发式）。"""
    import h5py
    import numpy as np  # noqa

    paths = {}

    def visit(name, obj):
        if isinstance(obj, h5py.Dataset):
            paths[name] = obj.shape

    with h5py.File(path, "r") as f:
        f.visititems(visit)
        top = list(f.keys())
        # robomimic 风格：data/demo_0, demo_1 ...
        n_ep = 0
        if "data" in f and isinstance(f["data"], h5py.Group):
            n_ep = sum(1 for k in f["data"].keys() if k.startswith("demo"))
        if n_ep == 0:
            n_ep = sum(1 for k in top if k.startswith(("demo", "episode", "traj")))

    # 找 action 维度
    dof = 0
    for k, shp in paths.items():
        if k.split("/")[-1] in ("action", "actions") and len(shp) >= 1:
            dof = int(shp[-1])
            break
    mods = []
    if any("image" in k or "rgb" in k or "camera" in k for k in paths):
        mods.append("rgb")
    if any(k.split("/")[-1] in ("state", "qpos", "observations") for k in paths):
        mods.append("state")

    fid = os.path.basename(path)
    return DatasetMeta(
        dataset_id=f"local/{fid}", name=fid, source="institutional",
        source_uri=os.path.abspath(path), source_format="hdf5",
        license_spdx="unknown", commercial_ok=False, redistribute_ok=False,
        provenance_type="teleop", embodiment=_guess_embodiment(""),
        dof=dof, modalities=mods, n_episodes=max(n_ep, 1),
        homepage="",
    )


# ================= 适配器 4：rosbag / MCAP（ROS 原生） =================
@register("mcap")
def from_mcap(path: str) -> DatasetMeta:
    """读本地 .mcap 文件的 summary（topic/schema/消息数），映射成目录项。"""
    from mcap.reader import make_reader

    topics, total_msgs = [], 0
    with open(path, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        if summary and summary.statistics:
            total_msgs = summary.statistics.message_count
        if summary:
            for ch in summary.channels.values():
                topics.append(ch.topic)

    mods = []
    joined = " ".join(topics).lower()
    if "image" in joined or "camera" in joined:
        mods.append("rgb")
    if "joint" in joined or "state" in joined:
        mods.append("state")
    if "depth" in joined:
        mods.append("depth")

    fid = os.path.basename(path)
    return DatasetMeta(
        dataset_id=f"local/{fid}", name=fid, source="institutional",
        source_uri=os.path.abspath(path), source_format="mcap",
        license_spdx="unknown", commercial_ok=False, redistribute_ok=False,
        provenance_type="teleop", embodiment=_guess_embodiment(""),
        modalities=mods, n_episodes=1, total_frames=total_msgs,
        homepage="",
    )
