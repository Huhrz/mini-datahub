"""
机器人数据领域现状报告（自动生成）
=====================================

把目录里的元数据自动提炼成"领域现状洞察"，让用户一眼看懂：
现在全球机器人数据是什么规模、集中在哪、缺什么、有什么风险。

原则（延续本项目一贯做法）：
  - 全部数字来自**目录里的真实数据**，不臆造；
  - 结论用**确定性规则**从数字推出，不是 AI 编的话；
  - 明确标注样本范围（"本目录收录的 N 个数据集"），不夸大成"全球全部"。
"""

import json
from collections import Counter


def _as_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v:
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else []
        except Exception:
            return []
    return []


def _pct(a, b):
    return round(100 * a / b, 1) if b else 0.0


def _top(counter, n=8):
    return [{"name": k, "count": v} for k, v in counter.most_common(n)]


def build(rows, coverage=None):
    """rows: datasets 表全部记录(dict 列表)。coverage: 可选的覆盖度统计。"""
    n = len(rows)
    if n == 0:
        return {"n": 0}

    total_ep = sum(int(r.get("n_episodes") or 0) for r in rows)
    total_fr = sum(int(r.get("total_frames") or 0) for r in rows)
    total_bytes = sum(int(r.get("size_bytes") or 0) for r in rows)
    hours = sum((float(r.get("duration_s") or 0)) for r in rows) / 3600.0

    src = Counter(str(r.get("source") or "unknown") for r in rows)
    fmt = Counter(str(r.get("source_format") or "unknown") for r in rows)
    emb = Counter(str(r.get("embodiment") or "unknown") for r in rows)

    mods = Counter()
    for r in rows:
        for m in _as_list(r.get("modalities")):
            mods[str(m)] += 1

    n_commercial = sum(1 for r in rows if r.get("commercial_ok"))
    n_unknown_lic = sum(1 for r in rows if str(r.get("license_spdx") or "unknown") in ("", "unknown"))
    n_failure = sum(1 for r in rows if r.get("has_failure_labels"))
    n_lang = sum(1 for r in rows if "language" in _as_list(r.get("modalities")))
    n_depth = sum(1 for r in rows if "depth" in _as_list(r.get("modalities")))
    n_unknown_prov = sum(1 for r in rows if str(r.get("provenance_type") or "") in ("", "unknown"))

    # 规模分布：数据集大小差异有多悬殊（长尾特征）
    eps = sorted((int(r.get("n_episodes") or 0) for r in rows), reverse=True)
    top10_ep = sum(eps[:10])
    buckets = Counter()
    for e in eps:
        if e < 100:
            buckets["<100 条"] += 1
        elif e < 1000:
            buckets["100–1k 条"] += 1
        elif e < 10000:
            buckets["1k–10k 条"] += 1
        else:
            buckets["≥10k 条"] += 1

    # 最大的几个数据集
    biggest = sorted(rows, key=lambda r: int(r.get("n_episodes") or 0), reverse=True)[:8]

    # 更新时间分布（数据新鲜度）
    years = Counter()
    for r in rows:
        d = str(r.get("last_modified") or "")
        if len(d) >= 4 and d[:4].isdigit():
            years[d[:4]] += 1

    # ---------------- 自动生成要点（规则推导，非编造） ----------------
    findings = []

    # 1) 集中度
    top_fmt, top_fmt_n = fmt.most_common(1)[0]
    if _pct(top_fmt_n, n) >= 40:
        findings.append({
            "type": "集中",
            "title": f"格式高度集中于 {top_fmt}",
            "detail": f"{top_fmt_n}/{n}（{_pct(top_fmt_n, n)}%）的数据集使用该格式，"
                      f"说明社区正在向统一格式收敛；但也意味着其它格式的数据接入门槛更高。",
        })
    top_emb, top_emb_n = emb.most_common(1)[0]
    findings.append({
        "type": "集中",
        "title": f"本体以 {top_emb} 为主",
        "detail": f"{top_emb_n}/{n}（{_pct(top_emb_n, n)}%）为该本体。"
                  f"其它本体的数据相对稀缺，跨本体迁移研究会受数据量限制。",
    })

    # 2) 长尾
    if total_ep:
        findings.append({
            "type": "长尾",
            "title": "数据规模极度不均衡",
            "detail": f"最大的 10 个数据集贡献了 {_pct(top10_ep, total_ep)}% 的轨迹量，"
                      f"其余 {n - 10} 个合计不到 {round(100 - _pct(top10_ep, total_ep), 1)}%。"
                      f"少数超大数据集主导了整个领域的数据供给。",
        })

    # 3) 语言标注
    findings.append({
        "type": "缺口" if _pct(n_lang, n) < 50 else "现状",
        "title": f"仅 {_pct(n_lang, n)}% 的数据集带语言指令",
        "detail": f"{n_lang}/{n} 含自然语言标注。训练 VLA（视觉-语言-动作）模型必须有语言，"
                  f"这是当前可用数据的主要瓶颈之一。",
    })

    # 4) 失败样本
    findings.append({
        "type": "缺口",
        "title": f"只有 {_pct(n_failure, n)}% 的数据集标注了失败样本",
        "detail": f"{n_failure}/{n} 含失败标注。绝大多数数据只记录成功演示，"
                  f"模型难以学会识别和纠正错误——这是鲁棒性研究的公认短板。",
    })

    # 5) 许可证风险
    findings.append({
        "type": "风险" if _pct(n_unknown_lic, n) > 20 else "现状",
        "title": f"{_pct(n_commercial, n)}% 可商用，{_pct(n_unknown_lic, n)}% 许可证不明",
        "detail": f"{n_commercial}/{n} 明确可商用；{n_unknown_lic} 个许可证未标明。"
                  f"许可证不清的数据在产品化时存在法律风险，学术研究通常影响较小。",
    })

    # 6) 采集方式透明度
    if _pct(n_unknown_prov, n) > 50:
        findings.append({
            "type": "风险",
            "title": f"{_pct(n_unknown_prov, n)}% 的数据集未说明采集方式",
            "detail": f"源站普遍不披露数据是遥操作、脚本还是仿真生成。"
                      f"采集方式直接影响数据分布与 sim2real 差距，是元数据治理的普遍短板。"
                      f"（我们对无法确认的一律标 unknown，不臆测。）",
        })

    # 7) 覆盖缺口
    if coverage:
        findings.append({
            "type": "缺口",
            "title": f"本体×任务 组合覆盖率仅 {coverage.get('coverage_pct', 0)}%",
            "detail": f"{coverage.get('covered', 0)}/{coverage.get('total_cells', 0)} 个组合有数据，"
                      f"{coverage.get('gap_count', 0)} 个组合全球空白。这些空白既可能是研究机会，"
                      f"也可能存在客观困难，需结合领域判断。",
        })

    return {
        "n": n,
        "scale": {
            "datasets": n,
            "episodes": total_ep,
            "frames": total_fr,
            "hours": round(hours, 1),
            "bytes": total_bytes,
        },
        "by_source": _top(src),
        "by_format": _top(fmt),
        "by_embodiment": _top(emb),
        "by_modality": _top(mods),
        "size_buckets": [{"name": k, "count": v} for k, v in
                         sorted(buckets.items(), key=lambda x: ["<100 条", "100–1k 条", "1k–10k 条", "≥10k 条"].index(x[0]))],
        "biggest": [{"dataset_id": r["dataset_id"], "name": r.get("name"),
                     "n_episodes": int(r.get("n_episodes") or 0),
                     "embodiment": r.get("embodiment"), "source": r.get("source")}
                    for r in biggest],
        "governance": {
            "commercial_ok": n_commercial, "commercial_pct": _pct(n_commercial, n),
            "license_unknown": n_unknown_lic, "license_unknown_pct": _pct(n_unknown_lic, n),
            "with_language": n_lang, "language_pct": _pct(n_lang, n),
            "with_failure": n_failure, "failure_pct": _pct(n_failure, n),
            "with_depth": n_depth, "depth_pct": _pct(n_depth, n),
            "provenance_unknown": n_unknown_prov, "provenance_unknown_pct": _pct(n_unknown_prov, n),
        },
        "freshness": [{"year": y, "count": c} for y, c in sorted(years.items())],
        "findings": findings,
        "note": f"本报告基于本平台当前收录的 {n} 个数据集自动统计，"
                f"不代表全球全部机器人数据；随目录更新自动刷新。",
    }
