"""
统一 taxonomy + 对齐引擎（B1 —— 文档点名最难、最值钱的护城河）
================================================================

解决的问题：各源对"任务/场景/本体/模态"的叫法五花八门
（grasp / pick-and-place / 抓取 全是一回事）。我们维护一套【受控词表】，
再用【对齐引擎】把任意原始叫法映射到统一概念 id —— 这样跨数据集检索才会"准"
（搜"抓取"能命中所有叫法不同但本质相同的数据集）。

特点（对应文档 B1）：
  - 受控词表 + 层级（技能原语 → 任务 → 长程）
  - 中英别名
  - 版本化（VERSION）
  - 对齐半自动化：精确别名命中 + 模糊匹配；匹配不上的标记"需人工复核"

纯标准库实现（difflib 做模糊匹配），不依赖网络/重型库。
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher

VERSION = "0.1.0"


@dataclass
class Concept:
    id: str                          # 统一概念 id（英文小写下划线）
    en: str                          # 英文名
    zh: str                          # 中文名
    parent: str = ""                 # 上级概念 id（构成层级）
    aliases: list = field(default_factory=list)   # 别名（中英、连字符、缩写等变体）


# ---------------- 受控词表 ----------------
TAXONOMY = {
    "tasks": [
        Concept("manipulation", "Manipulation", "操作", "", ["manipulate", "操控"]),
        Concept("pick_place", "Pick & Place", "抓取放置", "manipulation",
                ["pick and place", "pick-and-place", "pnp", "grasp", "grasping",
                 "pick", "抓取", "拾取", "抓放", "夹取"]),
        Concept("insertion", "Insertion / Assembly", "插入装配", "manipulation",
                ["insert", "peg insertion", "assembly", "assemble", "插入", "装配", "组装"]),
        Concept("pushing", "Pushing", "推动", "manipulation",
                ["push", "pusht", "push-t", "推", "推动"]),
        Concept("pouring", "Pouring", "倾倒", "manipulation",
                ["pour", "倒", "倒水", "倾倒"]),
        Concept("folding", "Folding", "折叠", "manipulation",
                ["fold", "fold clothes", "cloth folding", "折叠", "叠衣服", "叠"]),
        Concept("opening", "Opening", "开启", "manipulation",
                ["open", "open drawer", "open door", "打开", "开门", "开抽屉"]),
        Concept("stacking", "Stacking", "堆叠", "manipulation",
                ["stack", "stacking", "堆叠", "码放"]),
        Concept("long_horizon", "Long-horizon", "长程任务", "",
                ["long horizon", "multi-step", "multi step", "长程", "多步", "长时序"]),
        Concept("navigation", "Navigation", "导航", "",
                ["navigate", "nav", "move to", "导航", "移动"]),
    ],
    "scenes": [
        Concept("tabletop", "Tabletop", "桌面", "", ["table", "desktop", "tabletop_2d", "桌面", "台面"]),
        Concept("kitchen", "Kitchen", "厨房", "", ["厨房", "厨台"]),
        Concept("home", "Home", "家庭", "", ["household", "room", "domestic", "家庭", "居家", "房间"]),
        Concept("office", "Office", "办公室", "", ["办公室", "办公"]),
        Concept("factory", "Factory / Manufacturing", "工厂制造", "",
                ["manufacturing", "production", "assembly line", "工厂", "制造", "产线"]),
        Concept("commercial", "Commercial", "商业场所", "", ["commercial", "商业", "商场"]),
    ],
    "embodiments": [
        Concept("single_arm", "Single Arm", "单臂", "", ["single arm", "one arm", "单臂", "单机械臂"]),
        Concept("bimanual", "Bimanual", "双臂", "", ["dual arm", "dual-arm", "two arm", "双臂", "双机械臂"]),
        Concept("humanoid", "Humanoid", "人形", "", ["humanoid", "人形", "人形机器人"]),
        Concept("mobile", "Mobile Manipulator", "移动操作", "", ["mobile", "移动", "移动底盘"]),
        Concept("quadruped", "Quadruped", "四足", "", ["quadruped", "四足", "四足机器人"]),
    ],
    "modalities": [
        Concept("rgb", "RGB Image", "彩色图像", "", ["image", "camera", "video", "彩色", "图像", "视觉"]),
        Concept("depth", "Depth", "深度", "", ["depth map", "深度", "深度图"]),
        Concept("state", "Proprioceptive State", "本体状态", "",
                ["qpos", "proprioception", "joint state", "状态", "本体感知", "关节状态"]),
        Concept("language", "Language", "语言", "",
                ["instruction", "text", "language_instruction", "语言", "指令", "文本"]),
        Concept("tactile", "Tactile / Force", "触觉力觉", "", ["force", "tactile", "触觉", "力觉"]),
    ],
}


def _norm(s: str) -> str:
    return str(s).strip().lower().replace("_", " ").replace("-", " ")


# 预建别名索引：category -> {normalized_alias: concept}
_INDEX = {}
for cat, concepts in TAXONOMY.items():
    idx = {}
    for c in concepts:
        for token in [c.id, c.en, c.zh, *c.aliases]:
            idx[_norm(token)] = c
    _INDEX[cat] = idx


def align(raw: str, category: str, fuzzy_threshold: float = 0.82):
    """
    把一个原始标签对齐到受控词表里的统一概念。
    返回 dict: {raw, concept_id, concept_en, confidence, matched_by} 或 None（需人工复核）。
    matched_by: exact（精确别名命中）/ fuzzy（模糊匹配）。
    """
    if category not in _INDEX:
        raise ValueError(f"未知类别 {category}; 可选: {list(_INDEX)}")
    r = _norm(raw)
    idx = _INDEX[category]

    # 1) 精确别名命中
    if r in idx:
        c = idx[r]
        return {"raw": raw, "concept_id": c.id, "concept_en": c.en,
                "confidence": 1.0, "matched_by": "exact"}

    # 2) 模糊匹配（取与所有别名相似度最高者）
    best, best_score = None, 0.0
    for alias, c in idx.items():
        score = SequenceMatcher(None, r, alias).ratio()
        # 子串包含给予加分（"pick the cup" 含 "pick"）
        if r in alias or alias in r:
            score = max(score, 0.85)
        if score > best_score:
            best, best_score = c, score
    if best and best_score >= fuzzy_threshold:
        return {"raw": raw, "concept_id": best.id, "concept_en": best.en,
                "confidence": round(best_score, 2), "matched_by": "fuzzy"}

    return None   # 匹配不上 -> 需人工复核（半自动 + 人工兜底）


def align_many(raw_list, category):
    """对齐一批标签，返回 (已对齐的 concept_id 集合, 需人工复核的原始标签列表)。"""
    aligned, unresolved = set(), []
    for raw in raw_list or []:
        r = align(raw, category)
        if r:
            aligned.add(r["concept_id"])
        else:
            unresolved.append(raw)
    return aligned, unresolved


def concept_options(category):
    """给 UI 用：返回该类别下的 (concept_id, 显示名) 列表。"""
    return [(c.id, f"{c.zh} / {c.en}") for c in TAXONOMY.get(category, [])]
