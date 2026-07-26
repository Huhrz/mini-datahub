"""
问卷收集与自动统计（后台插件）
================================

用户在线填问卷 → 直接提交进数据库 → 后台自动聚合成可排序的 feature 优先级。
不需要任何人手动发送/整理结果。

聚合口径（与《用户反馈问卷》附录一致）：
  - C 节：重要性 − 满意度 = gap，越大越该优先做
  - D 节：字段重要性均值 → 该补哪些元数据
  - E 节：候选功能价值均值 + Top3 得票 → 直接产出开发顺序
  - B 节：任务完成率，未完成率 > 30% 视为【阻断级】，优先于一切新功能
  - H1：NPS = 推荐者(9-10)% − 贬损者(0-6)%
"""

import json
import uuid
import time

import store

# 题目定义（与问卷页一致，用于聚合时给出中文标签）
C_LABELS = {
    "C1": "跨源聚合", "C2": "跨语言语义检索", "C3": "分面筛选", "C4": "画廊按图浏览",
    "C5": "轨迹可视化回放", "C6": "元数据完整度", "C7": "质量分", "C8": "License 标注与门禁",
    "C9": "覆盖度地图与缺口报告", "C10": "相似数据集推荐", "C11": "训练清单导出",
    "C12": "评测基准链接", "C13": "Croissant 元数据", "C14": "账户与收藏集",
}
D_LABELS = {
    "D1a": "动作空间与约定", "D1b": "控制频率与时间同步", "D1c": "相机内外参标定",
    "D1d": "本体规格", "D1e": "成功/失败标注", "D1f": "语言指令质量",
    "D1g": "场景/物体多样性", "D1h": "采集方式", "D1i": "力觉/触觉",
    "D1j": "深度/点云", "D1k": "数据规模", "D1l": "许可证与再分发",
}
E_LABELS = {
    "E1a": "深度质检(抽样+置信区间)", "E1b": "近重复检测", "E1c": "OXE/RLDS 可视化",
    "E1d": "数据集横向对比", "E1e": "Python SDK / API Key", "E1f": "训练清单版本化与复现",
    "E1g": "动作空间自动换算", "E1h": "团队工作区", "E1i": "BibTeX 引用",
    "E1j": "社区提交数据集", "E1k": "变更订阅提醒", "E1l": "评测结果回链",
    "E1m": "按需子集下载", "E1n": "统计报告导出",
}
TASKS = {"B1a": "任务一 找双臂可商用数据", "B2a": "任务二 判断是否适用",
         "B3a": "任务三 可视化回放", "B4a": "任务四 导出训练清单"}
OPEN_Q = {"H3": "最希望增加的功能", "H4": "最困惑/受阻之处", "H5": "还差什么才能日常使用"}


def ensure_tables(con):
    store.run(con, "CREATE TABLE IF NOT EXISTS survey_responses "
                   "(id VARCHAR PRIMARY KEY, submitted_at VARCHAR, respondent VARCHAR, "
                   "org VARCHAR, contact VARCHAR, payload VARCHAR)")


def submit(con, answers: dict) -> str:
    rid = uuid.uuid4().hex
    a = answers or {}
    store.run(con, "INSERT INTO survey_responses VALUES (?, ?, ?, ?, ?, ?)",
              [rid, time.strftime("%Y-%m-%d %H:%M:%S"),
               str(a.get("R_name", ""))[:80], str(a.get("R_org", ""))[:120],
               str(a.get("R_contact", ""))[:120], json.dumps(a, ensure_ascii=False)])
    return rid


def _rows(con):
    out = []
    for r in store.run(con, "SELECT id, submitted_at, payload FROM survey_responses ORDER BY submitted_at"):
        try:
            out.append({"id": r[0], "at": r[1], "a": json.loads(r[2]) if r[2] else {}})
        except Exception:
            pass
    return out


def _num(v):
    try:
        f = float(v)
        return f if 0 <= f <= 10 else None
    except Exception:
        return None


def _mean(xs):
    return round(sum(xs) / len(xs), 2) if xs else None


def summarize(con) -> dict:
    rows = _rows(con)
    n = len(rows)
    if n == 0:
        return {"n": 0, "gap_ranking": [], "field_needs": [], "feature_ranking": [],
                "task_completion": [], "nps": None, "distributions": {}, "open_feedback": []}

    # ---- C 节：重要性 / 满意度 / gap ----
    gap = []
    for cid, label in C_LABELS.items():
        imp, sat = [], []
        for r in rows:
            v = r["a"].get(cid)
            if isinstance(v, dict):
                x = _num(v.get("重要性"));  imp.append(x) if x is not None else None
                y = _num(v.get("满意度"));  sat.append(y) if y is not None else None
        mi, ms = _mean(imp), _mean(sat)
        if mi is None and ms is None:
            continue
        g = round(mi - ms, 2) if (mi is not None and ms is not None) else None
        level = ("重点改进" if g is not None and g >= 1.5 else
                 "待改进" if g is not None and g >= 0.5 else
                 "过度投入" if g is not None and g < -0.5 else "基本匹配")
        gap.append({"id": cid, "label": label, "importance": mi, "satisfaction": ms,
                    "gap": g, "level": level, "n": max(len(imp), len(sat))})
    gap.sort(key=lambda x: (x["gap"] is None, -(x["gap"] or 0)))

    # ---- D 节：字段重要性 ----
    fields = []
    for did, label in D_LABELS.items():
        xs = [x for x in (_num(r["a"].get(did)) for r in rows) if x is not None]
        if xs:
            fields.append({"id": did, "label": label, "mean": _mean(xs), "n": len(xs)})
    fields.sort(key=lambda x: -x["mean"])

    # ---- E 节：候选功能价值 + Top3 得票 ----
    votes = {}
    for r in rows:
        for k, w in (("E2_1", 3), ("E2_2", 2), ("E2_3", 1)):
            v = str(r["a"].get(k, "")).strip()
            if v:
                votes[v] = votes.get(v, 0) + w
    feats = []
    for eid, label in E_LABELS.items():
        xs = [x for x in (_num(r["a"].get(eid)) for r in rows) if x is not None]
        feats.append({"id": eid, "label": label, "mean": _mean(xs) or 0,
                      "n": len(xs), "top3_score": votes.get(eid, 0)})
    feats.sort(key=lambda x: (-(x["mean"] or 0), -x["top3_score"]))

    # ---- B 节：任务完成率 ----
    tasks = []
    for tid, label in TASKS.items():
        vals = [str(r["a"].get(tid, "")) for r in rows if r["a"].get(tid)]
        if not vals:
            continue
        tot = len(vals)
        ok = sum(1 for v in vals if v.startswith("顺利"))
        fail = sum(1 for v in vals if v.startswith("未能") or v.startswith("没找到"))
        tasks.append({"id": tid, "label": label, "n": tot,
                      "success_rate": round(100 * ok / tot),
                      "fail_rate": round(100 * fail / tot),
                      "blocking": (100 * fail / tot) > 30})

    # ---- NPS ----
    scores = [x for x in (_num(r["a"].get("H1")) for r in rows) if x is not None]
    nps = None
    if scores:
        pro = sum(1 for s in scores if s >= 9)
        det = sum(1 for s in scores if s <= 6)
        nps = {"score": round(100 * (pro - det) / len(scores)), "n": len(scores),
               "mean": _mean(scores)}

    # ---- 单/多选分布 ----
    dist = {}
    for r in rows:
        for k, v in r["a"].items():
            if k.startswith(("C", "D1", "E1", "E2", "R_", "H1", "H3", "H4", "H5")):
                continue
            if isinstance(v, dict):
                continue
            vals = v if isinstance(v, list) else [v]
            for x in vals:
                dist.setdefault(k, {})
                dist[k][str(x)] = dist[k].get(str(x), 0) + 1

    # ---- 开放题 ----
    openfb = []
    for r in rows:
        for q, label in OPEN_Q.items():
            t = str(r["a"].get(q, "")).strip()
            if t:
                openfb.append({"at": r["at"], "q": q, "label": label, "text": t,
                               "who": str(r["a"].get("R_name", "") or "匿名"),
                               "role": str(r["a"].get("A1", "") or "")})

    return {"n": n, "gap_ranking": gap, "field_needs": fields, "feature_ranking": feats,
            "task_completion": tasks, "nps": nps, "distributions": dist,
            "open_feedback": openfb}


def export_rows(con):
    """导出全部原始回答（供离线分析）。"""
    return [{"id": r["id"], "submitted_at": r["at"], **r["a"]} for r in _rows(con)]
