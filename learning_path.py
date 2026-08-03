"""
学习路径（学生引导 · 入门向导）
==================================

给刚接触机器人数据的学生一条"从看懂到跑通"的路径。每一步都：
  - 讲清这一步要理解什么（概念）
  - 给出**站内可直接操作**的动作（去哪个页面、点什么）
  - 挂上**真实数据集**（从目录里按条件动态挑，不写死）
  - 留一个自检问题，确认真的学会了

设计原则：不空谈理论，每步都能在这个平台上真做一遍。
"""

STEPS = [
    {
        "id": "S1",
        "title": "第 1 步 · 看懂一个数据集",
        "goal": "理解一条机器人数据到底长什么样。",
        "learn": [
            "一条**轨迹（episode）**= 机器人完整做一次任务的记录。",
            "每一帧同时包含：相机图像、机器人状态（关节角/末端位姿）、要执行的动作。",
            "所谓“训练机器人”，本质是学一个从「看到的画面 + 任务指令」到「该输出什么动作」的映射。",
        ],
        "do": "打开任意一个数据集详情页 → 看「内容预览」的截图 → 再点开可视化，"
              "观察视频与下方的状态/动作曲线是如何**逐帧对应**的。",
        "check": "你能说出：这条轨迹里机器人在做什么？动作曲线的每条线代表什么？",
        "pick": {"embodiment": "single_arm", "max_episodes": 500, "need_video": True},
        "terms": ["n_episodes", "modalities", "total_frames"],
    },
    {
        "id": "S2",
        "title": "第 2 步 · 理解动作空间（最关键的一课）",
        "goal": "搞清动作数值到底代表什么，避免最常见的踩坑。",
        "learn": [
            "**关节空间（joint）**：直接控制每个关节转到多少度。",
            "**末端空间（cartesian/EE）**：控制夹爪在三维空间中的位置和姿态，更直观但需要逆运动学。",
            "**绝对 vs 增量**：绝对是“移动到这个位置”，增量是“相对现在再移动这么多”。",
            "两份数据即使任务一样，如果动作约定不同，**直接混在一起训练会让模型学乱**。",
        ],
        "do": "对比两个数据集的「动作约定」字段：找一个关节控制的、一个末端控制的，"
              "看它们的动作维度（dof）和曲线形态有何不同。",
        "check": "给你一份新数据，你知道该看哪个字段判断它能不能和手头数据混用吗？",
        "pick": {"has_convention": True},
        "terms": ["action_convention", "dof", "fps"],
    },
    {
        "id": "S3",
        "title": "第 3 步 · 判断数据能不能用",
        "goal": "学会在**不下载**的前提下评估一份数据。",
        "learn": [
            "先看**本体**是否匹配你的机器人——不匹配的数据迁移代价很高。",
            "再看**模态**是否齐全：要训 VLA 就必须有语言指令，否则只能做单任务模仿。",
            "看**规模**：轨迹数、总帧数、平均每集长度，判断够不够训、要训多久。",
            "看**许可证**：带 NC 的不可商用；做产品前必须确认。",
            "质量分只是**元数据初筛**，不能替代亲眼看几条轨迹。",
        ],
        "do": "用左侧筛选器：选一个本体 + 一个任务概念 + 勾上「仅可商用」，"
              "看看还剩几个数据集。再打开其中一个，逐项核对上面 5 点。",
        "check": "你能用一句话说清：这个数据集适合谁、不适合谁？",
        "pick": {"commercial_only": True, "need_language": True},
        "terms": ["embodiment", "modalities", "license_spdx", "quality_score", "provenance_type"],
    },
    {
        "id": "S4",
        "title": "第 4 步 · 认识不同的数据格式",
        "goal": "知道拿到数据后该用什么工具打开。",
        "learn": [
            "**LeRobot**（HuggingFace 生态）：目前最主流，视频 + parquet，工具链最完善。",
            "**RLDS/TFDS**（Open X-Embodiment）：Google 生态，tfrecord 存储，需要 tensorflow_datasets。",
            "**HDF5**：各实验室自定义常用（RoboMimic、ALOHA），用 h5py 读。",
            "**MCAP/rosbag**：ROS 原生记录格式。",
            "格式不统一正是这个领域最大的摩擦点——也是这个平台做归一化的原因。",
        ],
        "do": "在「源格式」筛选器里逐个切换，看不同格式的数据集在元数据上有何差异。",
        "check": "遇到一个 RLDS 数据集，你知道它和 LeRobot 数据集在使用上差在哪吗？",
        "pick": {"diverse_formats": True},
        "terms": ["source_format"],
    },
    {
        "id": "S5",
        "title": "第 5 步 · 组一份训练数据集合",
        "goal": "从“看数据”进阶到“为训练选数据”。",
        "learn": [
            "真实训练很少只用一个数据集，而是**混采（data mixture）**多个来源。",
            "混采要注意：本体是否兼容、动作约定是否一致、各数据集的采样权重怎么配。",
            "同时要守住合规底线：非商用数据不能混进商业训练。",
            "选型过程要**可复现**——记录用了哪些数据、什么版本、什么比例。",
        ],
        "do": "把几个数据集加入「训练集」→ 点「导出训练清单」，"
              "看看生成的 JSON 里有什么（源地址、权重、license 提示）。",
        "check": "这份清单交给同学，他能复现出和你一样的数据组合吗？",
        "pick": {"commercial_only": True, "limit": 4},
        "terms": ["license_spdx", "action_convention"],
    },
    {
        "id": "S6",
        "title": "第 6 步 · 找到研究空白",
        "goal": "从使用者视角，升级到研究者视角。",
        "learn": [
            "把所有数据按「本体 × 任务」铺开，就能看到哪些组合**全球都缺数据**。",
            "空白可能是机会（没人做过），也可能是难点（做不了或没价值）——需要你判断。",
            "选题时，数据可得性往往比想法本身更决定成败。",
        ],
        "do": "打开「覆盖度地图」标签页，看热力图和下方的「数据缺口报告」，"
              "找出 1~2 个你觉得值得研究的空白组合。",
        "check": "你能解释为什么那个格子是空的吗？是没人做，还是有客观困难？",
        "pick": None,
        "terms": ["coverage", "concept"],
    },
]


def _row_ok(r, rule):
    """按规则判断某数据集是否适合作为该步的示例。"""
    if not rule:
        return False
    if rule.get("embodiment") and r.get("embodiment") != rule["embodiment"]:
        return False
    if rule.get("max_episodes") and (r.get("n_episodes") or 0) > rule["max_episodes"]:
        return False
    if rule.get("commercial_only") and not r.get("commercial_ok"):
        return False
    if rule.get("need_video") and not (r.get("n_cameras") or 0):
        return False
    if rule.get("need_language"):
        mods = r.get("modalities") or []
        if "language" not in mods:
            return False
    if rule.get("has_convention") and not r.get("action_convention"):
        return False
    return True


def build(rows):
    """给每一步挑几个真实数据集作示例。rows = 目录里的数据集列表(dict)。"""
    out = []
    for s in STEPS:
        examples = []
        rule = s.get("pick")
        if rule:
            if rule.get("diverse_formats"):
                # 每种格式各挑一个，体现格式差异
                seen = set()
                for r in rows:
                    f = str(r.get("source_format", ""))
                    key = f.split("_")[0]
                    if key and key not in seen and (r.get("n_episodes") or 0) > 0:
                        seen.add(key)
                        examples.append(r)
                    if len(examples) >= 4:
                        break
            else:
                lim = rule.get("limit", 3)
                for r in rows:
                    if _row_ok(r, rule):
                        examples.append(r)
                    if len(examples) >= lim:
                        break
        out.append({
            **{k: v for k, v in s.items() if k != "pick"},
            "examples": [{"dataset_id": e["dataset_id"], "name": e.get("name"),
                          "embodiment": e.get("embodiment"),
                          "source_format": e.get("source_format"),
                          "n_episodes": e.get("n_episodes")} for e in examples],
        })
    return out
