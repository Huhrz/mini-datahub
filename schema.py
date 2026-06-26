"""
迷你 DataHub —— 机器人轨迹元数据 Schema（项目的核心资产）
=============================================================

这张 schema 是整个 DataHub 的"发动机"：检索、按许可过滤、挑数据、配比
全都靠它驱动。脚本会从任何数据集里抽取这些字段，统一存进 DuckDB 目录。

设计原则：
  - 字段尽量"格式无关"，无论源数据是 RLDS / LeRobot / HDF5 都能填。
  - 区分【数据集级】和【轨迹级】两层（一个数据集含很多条轨迹）。
  - 把"许可证""成功/失败""本体"做成一等字段（这是 DataHub 的差异化点）。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------- 数据集级元数据（一个数据集一行）----------
@dataclass
class DatasetMeta:
    dataset_id: str            # 全局唯一 id，如 "lerobot/aloha_sim_insertion_human"
    name: str                  # 人类可读名称
    source: str                # 来源：huggingface / openx / agibot / robomind ...
    source_format: str         # 原始格式：lerobot_v3 / rlds / hdf5 / zarr / rosbag
    license: str               # 许可证，如 "apache-2.0" / "cc-by-nc-sa-4.0"
    commercial_use: bool       # 能否商用（从 license 推断，做成一等字段）
    n_episodes: int            # 轨迹条数
    total_frames: int          # 总帧数
    fps: float                 # 控制/采样频率
    embodiment: str            # 本体：single_arm / bimanual / humanoid / mobile / quadruped
    robot_model: str = ""      # 机器人型号，如 "aloha" / "franka" / "agibot_g2"
    n_cameras: int = 0         # 摄像头数量
    has_failure_labels: bool = False  # 是否含失败标注（高价值）
    collection: str = ""       # 采集方式：teleop / sim / human_video / autonomous
    homepage: str = ""         # 主页/引用链接

    def to_row(self):
        return asdict(self)


# ---------- 轨迹级元数据（一条轨迹一行）----------
@dataclass
class EpisodeMeta:
    episode_uid: str           # 全局唯一，如 "{dataset_id}#{episode_index}"
    dataset_id: str            # 外键，指向所属数据集
    episode_index: int         # 在该数据集内的序号
    length: int                # 帧数
    duration_s: float          # 时长（秒）
    task_text: str = ""        # 任务的自然语言描述，如 "put the cup on the shelf"
    embodiment: str = ""       # 冗余存一份，方便单表检索
    success: Optional[bool] = None  # True/False/None(未标注)
    action_dim: int = 0        # 动作维度
    state_dim: int = 0         # 状态维度

    def to_row(self):
        return asdict(self)


# ---------- 许可证 -> 是否可商用 的简单推断 ----------
NON_COMMERCIAL_KEYWORDS = ("nc", "non-commercial", "noncommercial", "research-only")

def infer_commercial_use(license_str: str) -> bool:
    """粗略判断：许可证里含 'nc' 等字样则视为不可商用。真实项目应人工复核。"""
    if not license_str:
        return False  # 未知许可证，保守起见当作不可商用
    s = license_str.lower()
    return not any(k in s for k in NON_COMMERCIAL_KEYWORDS)


# DuckDB 建表语句（与上面的 dataclass 字段一一对应）
CREATE_DATASETS_TABLE = """
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id        VARCHAR PRIMARY KEY,
    name              VARCHAR,
    source            VARCHAR,
    source_format     VARCHAR,
    license           VARCHAR,
    commercial_use    BOOLEAN,
    n_episodes        INTEGER,
    total_frames      BIGINT,
    fps               DOUBLE,
    embodiment        VARCHAR,
    robot_model       VARCHAR,
    n_cameras         INTEGER,
    has_failure_labels BOOLEAN,
    collection        VARCHAR,
    homepage          VARCHAR
);
"""

CREATE_EPISODES_TABLE = """
CREATE TABLE IF NOT EXISTS episodes (
    episode_uid    VARCHAR PRIMARY KEY,
    dataset_id     VARCHAR,
    episode_index  INTEGER,
    length         INTEGER,
    duration_s     DOUBLE,
    task_text      VARCHAR,
    embodiment     VARCHAR,
    success        BOOLEAN,
    action_dim     INTEGER,
    state_dim      INTEGER
);
"""
