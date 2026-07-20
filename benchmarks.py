"""
评测出口链接（G4 雏形）—— 把数据集接到适用的评测基准
========================================================

对齐设计文档 G4：由目录项跳转到适用 benchmark，打通"发现 → 训练 → 评测"。
这里做**规则匹配雏形**：按数据集的本体 + 任务概念，推荐适用的公开评测基准并回链
其项目/榜单页面。基准信息为公开事实（项目主页），非 AI 编造。

注意（对齐文档风险条目）：不同 benchmark 的协议不完全可比，这里只做"适用性"链接，
不做跨基准的误导性排名。
"""

# 每条：真实公开基准。embodiments 为空=不限；concepts 为空=任意操作任务。
BENCHMARKS = [
    {"name": "LIBERO", "url": "https://libero-project.github.io/",
     "embodiments": {"single_arm"},
     "concepts": {"pick_place", "manipulation", "long_horizon", "stacking", "pushing", "opening"},
     "sim": True, "desc": "终身学习操作基准（4 个任务套件）"},
    {"name": "CALVIN", "url": "http://calvin.cs.uni-freiburg.de/",
     "embodiments": {"single_arm"},
     "concepts": {"long_horizon", "manipulation", "pushing", "opening", "stacking"},
     "sim": True, "desc": "语言条件长程操作"},
    {"name": "Meta-World", "url": "https://meta-world.github.io/",
     "embodiments": {"single_arm"},
     "concepts": {"manipulation", "pick_place", "pushing", "opening", "pressing"},
     "sim": True, "desc": "50 任务多任务操作（MT50/ML45）"},
    {"name": "RLBench", "url": "https://sites.google.com/view/rlbench",
     "embodiments": {"single_arm"}, "concepts": set(),
     "sim": True, "desc": "100+ 任务操作基准"},
    {"name": "ManiSkill", "url": "https://www.maniskill.ai/",
     "embodiments": {"single_arm", "bimanual"}, "concepts": set(),
     "sim": True, "desc": "大规模操作 + 物理仿真"},
    {"name": "RoboCasa", "url": "https://robocasa.ai/",
     "embodiments": {"mobile", "single_arm"},
     "concepts": {"cooking", "cleaning", "opening", "pick_place", "pouring"},
     "sim": True, "desc": "厨房移动操作"},
    {"name": "SIMPLER", "url": "https://simpler-env.github.io/",
     "embodiments": {"single_arm"}, "concepts": set(),
     "sim": True, "desc": "真实数据(OXE fractal/bridge)的真到仿评测"},
    {"name": "RoboTwin", "url": "https://robotwin-benchmark.github.io/",
     "embodiments": {"bimanual"}, "concepts": set(),
     "sim": True, "desc": "双臂协作操作基准"},
]


def match(embodiment: str = "", concepts=None, dataset_id: str = "", source: str = ""):
    """按本体 + 任务概念匹配适用基准。返回 [{name,url,desc,sim,why}]。"""
    cset = set(concepts or [])
    did = (dataset_id or "").lower()
    out = []
    for b in BENCHMARKS:
        if b["embodiments"] and embodiment and embodiment not in b["embodiments"]:
            continue
        if b["concepts"] and cset and not (b["concepts"] & cset):
            continue
        # SIMPLER 特案：只对 OXE 的 fractal/bridge/rt 类真实数据推荐
        if b["name"] == "SIMPLER" and not (
                source == "openx" or any(k in did for k in ("fractal", "bridge", "rt_1", "rt1"))):
            continue
        why = []
        if b["embodiments"] and embodiment in b["embodiments"]:
            why.append(f"本体={embodiment}")
        if b["concepts"] and (b["concepts"] & cset):
            why.append("任务：" + "、".join(sorted(b["concepts"] & cset))[:40])
        out.append({"name": b["name"], "url": b["url"], "desc": b["desc"],
                    "sim": b["sim"], "why": " · ".join(why) or "本体适配"})
    return out
