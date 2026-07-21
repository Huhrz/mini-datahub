"""
后台运维 / 接入 Agent（原型）
================================

比"定时脚本"更进一步：跑完刷新流水线后，**读目录状态 → 用 LLM 分析 → 写运维摘要**
（本轮新增了什么、有哪些异常需要注意、给出建议行动），存成报告。

设计：
  - 确定性部分（接入/健康检查/统计）永远能跑，不依赖 LLM。
  - "智能摘要"部分：若配了 ANTHROPIC_API_KEY 就调 LLM 写自然语言摘要；
    没配就退回模板摘要。可用 ANTHROPIC_BASE_URL 指向代理/兼容端点（国内可用）。

用法：
    python agent_ops.py                 # 跑一轮：刷新 + 生成运维摘要
    python agent_ops.py --no-ingest     # 只体检+出摘要，不接入新数据
环境变量：
    ANTHROPIC_API_KEY   配了才启用 LLM 摘要（否则模板摘要）
    ANTHROPIC_BASE_URL  默认 https://api.anthropic.com（可指向代理）
    ANTHROPIC_MODEL     默认 claude-haiku-4-5-20251001
    MDH_INGEST_LIMIT / MDH_INGEST_TASK / MDH_INGEST_AUTHORS  接入范围
"""

import os
import json
import time
import argparse

import store
import taxonomy as tx


def _snapshot_ids(con):
    try:
        return set(r[0] for r in store.run(con, "SELECT dataset_id FROM datasets"))
    except Exception:
        return set()


def gather_state(con):
    """读目录关键状态（纯确定性）。"""
    st = {}
    st["total"] = store.one(con, "SELECT COUNT(*) FROM datasets")[0]
    st["by_source"] = {r[0]: r[1] for r in store.run(
        con, "SELECT source, COUNT(*) FROM datasets GROUP BY source ORDER BY 2 DESC")}
    st["by_format"] = {r[0]: r[1] for r in store.run(
        con, "SELECT source_format, COUNT(*) FROM datasets GROUP BY source_format ORDER BY 2 DESC")}
    st["non_commercial"] = store.one(
        con, "SELECT COUNT(*) FROM datasets WHERE commercial_ok = false")[0]
    # 链接健康
    try:
        st["links_dead"] = store.one(con, "SELECT COUNT(*) FROM link_health WHERE alive = false")[0]
        st["links_checked"] = store.one(con, "SELECT COUNT(*) FROM link_health")[0]
        st["dead_examples"] = [r[0] for r in store.run(
            con, "SELECT dataset_id FROM link_health WHERE alive = false LIMIT 8")]
    except Exception:
        st["links_dead"] = st["links_checked"] = 0
        st["dead_examples"] = []
    # 覆盖度 / 缺口
    concepts = tx.concept_options("tasks")
    cids = [c for c, _ in concepts]
    labels = {c: l for c, l in concepts}
    tag = {}
    try:
        for did, cid in store.run(con, "SELECT dataset_id, concept_id FROM concept_tags WHERE category='tasks'"):
            tag.setdefault(cid, 0)
            tag[cid] += 1
    except Exception:
        pass
    totals = sorted(({"c": labels[c], "n": tag.get(c, 0)} for c in cids), key=lambda x: x["n"])
    st["scarcest_concepts"] = totals[:6]
    st["concepts_uncovered"] = sum(1 for c in cids if tag.get(c, 0) == 0)
    st["concepts_total"] = len(cids)
    return st


def _facts_text(state, new_ids, ts):
    lines = [
        f"时间：{ts}",
        f"目录数据集总数：{state['total']}",
        f"按来源：{state['by_source']}",
        f"按格式：{state['by_format']}",
        f"非商用数据集数：{state['non_commercial']}",
        f"链接体检：已检查 {state['links_checked']}，失效 {state['links_dead']}，失效示例 {state['dead_examples']}",
        f"任务概念覆盖：{state['concepts_total'] - state['concepts_uncovered']}/{state['concepts_total']} 有数据，"
        f"{state['concepts_uncovered']} 个全球空缺",
        f"最稀缺概念（全球数据集数）：{[(x['c'].split(' / ')[0], x['n']) for x in state['scarcest_concepts']]}",
        f"本轮新增数据集 {len(new_ids)} 个：{sorted(new_ids)[:15]}",
    ]
    return "\n".join(lines)


_SYS_PROMPT = ("你是机器人数据 hub 的运维助手。根据给定的目录状态事实，用中文写一份简洁的"
               "运维摘要：①本轮变化 ②需要注意的异常（失效链接/非商用/数据缺口）③3 条以内"
               "建议行动。只依据给定事实，不编造数字。")


def llm_digest(facts_text):
    """OpenAI 兼容接口（通义千问/DeepSeek/OpenAI 等都适用）。没配 key/base 就返回 None。
    环境变量：MDH_LLM_BASE_URL / MDH_LLM_API_KEY / MDH_LLM_MODEL。"""
    key = os.environ.get("MDH_LLM_API_KEY")
    base = os.environ.get("MDH_LLM_BASE_URL", "").strip().rstrip("/")
    model = os.environ.get("MDH_LLM_MODEL", "qwen-plus")
    if not (key and base):
        return None
    try:
        import requests
        r = requests.post(
            f"{base}/chat/completions", timeout=60,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model, "max_tokens": 1024,
                "messages": [
                    {"role": "system", "content": _SYS_PROMPT},
                    {"role": "user", "content": facts_text},
                ],
            })
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[llm] 调用失败，退回模板摘要：{repr(e)[:120]}")
        return None


def template_digest(state, new_ids):
    """无 LLM 时的模板摘要。"""
    lines = ["## 运维摘要（模板）", ""]
    lines.append(f"- 目录共 **{state['total']}** 个数据集；本轮新增 **{len(new_ids)}** 个。")
    if state["links_dead"]:
        lines.append(f"- ⚠️ 链接失效 **{state['links_dead']}** 个（示例：{state['dead_examples'][:5]}），建议核查或降级。")
    if state["non_commercial"]:
        lines.append(f"- 非商用数据集 **{state['non_commercial']}** 个，导出训练清单时受 license 门禁保护。")
    if state["concepts_uncovered"]:
        scarce = [x["c"].split(" / ")[0] for x in state["scarcest_concepts"] if x["n"] == 0]
        lines.append(f"- 任务概念有 **{state['concepts_uncovered']}** 个全球空缺，最缺：{scarce or '—'}；建议定向补采。")
    if new_ids:
        lines.append(f"- 新增：{sorted(new_ids)[:15]}")
    return "\n".join(lines)


def run_once(args):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1) 接入前快照
    con = store.connect(read_only=not store.is_pg())
    before = _snapshot_ids(con)
    store.close(con)

    # 2) 跑刷新流水线（接入 + 健康检查）
    if not args.no_ingest:
        try:
            import pipeline
            pipeline.run()
        except Exception as e:
            print(f"[pipeline] 出错（继续出摘要）：{repr(e)[:120]}")

    # 3) 接入后读状态
    con = store.connect(read_only=not store.is_pg())
    after = _snapshot_ids(con)
    state = gather_state(con)
    store.close(con)
    new_ids = after - before

    # 4) 生成摘要（LLM 优先，模板兜底）
    facts = _facts_text(state, new_ids, ts)
    digest = llm_digest(facts) or template_digest(state, new_ids)

    # 5) 存报告
    outdir = os.environ.get("MDH_REPORT_DIR", "reports")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"ops_{time.strftime('%Y%m%d_%H%M')}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 运维摘要 {ts}\n\n{digest}\n\n---\n\n<details><summary>原始事实</summary>\n\n```\n{facts}\n```\n</details>\n")
    print("\n" + "=" * 60)
    print(digest)
    print("=" * 60)
    print(f"[ok] 报告已存：{path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ingest", action="store_true", help="跳过接入，只体检+出摘要")
    ap.add_argument("--loop", action="store_true", help="常驻：每 MDH_SCHEDULE_HOURS 小时跑一轮")
    args = ap.parse_args()
    if args.loop:
        hours = float(os.environ.get("MDH_SCHEDULE_HOURS", "24"))
        print(f"[agent] 常驻运维 agent 启动，每 {hours} 小时跑一轮。")
        while True:
            try:
                run_once(args)
            except Exception as e:
                print(f"[agent] 本轮出错（继续）：{repr(e)[:150]}")
            time.sleep(hours * 3600)
    else:
        run_once(args)


if __name__ == "__main__":
    main()
