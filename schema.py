"""
迷你 DataHub —— 联邦目录项（Catalog Entry）Schema
==================================================

对齐系统设计文档 v0.1 第 4.1 节的 Catalog Entry。核心理念（文档第 1 章）：
  - 元数据与数据分离：目录项是"一等公民"，持有归一化元数据 + 标签 + 质量分
    + 溯源 + license，只**指向**数据，不绑定/不搬运数据本体。
  - License 感知默认开：每项必须带机器可读的许可与可商用/可分发标记。
  - 动作约定只描述、不强转（文档 4.3）：保留 action_convention 元数据，
    统一的是"描述方式"，不是"数值表示"，下游训练按需转换。

为避免"建表/插入字段数对不上"的 bug，本文件让 CREATE TABLE 和 INSERT 语句
都【从 dataclass 字段定义自动生成】，加字段只改 dataclass 一处即可。
"""

import json
from dataclasses import dataclass, field, asdict, fields


# ============ 数据集级目录项（Catalog Entry）============
@dataclass
class DatasetMeta:
    # --- 标识 ---
    dataset_id: str                 # = 文档的 entry_id，全局唯一
    name: str
    source: str = ""                # huggingface / openx / agibot / robomind ...
    source_uri: str = ""            # 联邦指针：指向数据原始位置（不搬运）
    version: str = "v1"
    source_format: str = ""         # lerobot_v3 / rlds / hdf5 / zarr / rosbag

    # --- 治理：license / 质量 / 溯源（文档 4.1 治理段）---
    license_spdx: str = "unknown"   # SPDX 标识，如 apache-2.0 / cc-by-nc-sa-4.0
    commercial_ok: bool = False     # 是否可商用
    redistribute_ok: bool = False   # 是否可再分发
    quality_score: float = -1.0     # 质量分 0~1；-1 表示未评分（B4 自动质检）
    learnability_score: float = -1.0  # 可学性/信息量 0~1；-1 表示未评分
    quality_report: dict = field(default_factory=dict)  # 质检细项明细（可解释）
    provenance_type: str = ""       # teleop / kinesthetic / sim / autonomous / human_video

    # --- 本体（embodiment 结构拆开存，便于检索）---
    embodiment: str = ""            # single_arm / bimanual / humanoid / mobile / quadruped
    robot_model: str = ""
    dof: int = 0                    # 自由度
    arms: int = 0
    end_effector: str = ""          # gripper / dexterous_hand / suction ...
    base: str = "fixed"             # fixed / mobile

    # --- 动作约定（文档 4.3：只描述不强转）---
    action_convention: dict = field(default_factory=dict)
    # 例：{"space":"joint", "frame":"base", "abs_or_delta":"delta", "units":"rad"}

    # --- taxonomy 标签（挂统一本体；这里先存字符串列表）---
    tasks: list = field(default_factory=list)      # 技能原语→任务→长程
    scenes: list = field(default_factory=list)
    modalities: list = field(default_factory=list) # rgb / depth / state / language ...

    # --- 技术规格 ---
    fps: float = 0.0
    n_cameras: int = 0
    n_episodes: int = 0
    total_frames: int = 0
    duration_s: float = 0.0

    # --- 发现 / 溯源辅助 ---
    has_failure_labels: bool = False
    croissant_ref: str = ""         # 对外 Croissant 记录的引用（G5 生成）
    dedup_cluster_id: str = ""      # 近重复聚类 id（B4）
    linked_benchmarks: list = field(default_factory=list)  # 适用的评测基准
    homepage: str = ""

    def to_row(self):
        return asdict(self)


# ============ 轨迹级元数据 ============
@dataclass
class EpisodeMeta:
    episode_uid: str
    dataset_id: str
    episode_index: int
    length: int
    duration_s: float
    task_text: str = ""
    embodiment: str = ""
    success: bool = None            # True/False/None(未标注)
    action_dim: int = 0
    state_dim: int = 0

    def to_row(self):
        return asdict(self)


# ============ 通用：从 dataclass 自动生成建表 / 插入 ============
# Python 类型 -> DuckDB 列类型；list/dict 以 JSON 文本存进 VARCHAR
_PY_TO_SQL = {str: "VARCHAR", bool: "BOOLEAN", int: "BIGINT", float: "DOUBLE"}
_JSON_TYPES = (list, dict)


def _col_type(py_type):
    if py_type in _JSON_TYPES:
        return "VARCHAR"          # 存 JSON 字符串
    return _PY_TO_SQL.get(py_type, "VARCHAR")


def create_table_sql(table: str, dc, primary_key: str) -> str:
    cols = []
    for f in fields(dc):
        sql = _col_type(f.type)
        if f.name == primary_key:
            sql += " PRIMARY KEY"
        cols.append(f"    {f.name} {sql}")
    return f"CREATE TABLE IF NOT EXISTS {table} (\n" + ",\n".join(cols) + "\n);"


def insert_sql(table: str, dc) -> str:
    n = len(fields(dc))
    return f"INSERT INTO {table} VALUES (" + ",".join(["?"] * n) + ")"


def to_db_values(meta) -> tuple:
    """把一个 dataclass 实例转成可插入的值；list/dict 字段转成 JSON 文本。"""
    row = asdict(meta)
    out = []
    for f in fields(meta):
        v = row[f.name]
        if f.type in _JSON_TYPES:
            v = json.dumps(v, ensure_ascii=False)
        out.append(v)
    return tuple(out)


# 预生成两张表的建表语句（供各脚本 import）
CREATE_DATASETS_TABLE = create_table_sql("datasets", DatasetMeta, "dataset_id")
CREATE_EPISODES_TABLE = create_table_sql("episodes", EpisodeMeta, "episode_uid")


# ============ License 推断助手 ============
NON_COMMERCIAL_KEYWORDS = ("nc", "non-commercial", "noncommercial", "research-only")


def license_fields(license_str: str):
    """从许可证字符串推断 (spdx, commercial_ok, redistribute_ok)。真实项目需法务复核。"""
    spdx = license_str or "unknown"
    s = (license_str or "").lower()
    parts = s.replace(".", "-").split("-")
    has_license = bool(license_str) and s != "unknown"
    commercial_ok = has_license and not any(k in s for k in NON_COMMERCIAL_KEYWORDS)
    redistribute_ok = has_license and "nd" not in parts   # ND = 禁止演绎/再分发
    return spdx, commercial_ok, redistribute_ok


def infer_commercial_use(license_str: str) -> bool:
    """兼容旧接口。"""
    return license_fields(license_str)[1]
