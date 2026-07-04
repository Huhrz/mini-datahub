"""
FastAPI 后端 —— 把目录数据暴露成 JSON API（前后端分离的地基）
================================================================

复用 hub_data.py / taxonomy.py 的逻辑，对外提供干净的 JSON 接口，
前端（React）通过这些接口拿数据。前端换成任何技术都不用动后端。

启动：
    pip install fastapi uvicorn
    uvicorn api:app --reload --port 8000
文档：浏览器打开 http://localhost:8000/docs 可交互测试所有接口。
"""

import os
import json
import threading

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import hub_data as hd
import taxonomy as tx

app = FastAPI(title="RoboticDataHub API", version="0.1.0")

# 允许前端（localhost:5173 等）跨域访问
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)


def _open_catalog():
    """优先只读打开（后端只读数据、不占写锁，减少和其它进程抢锁）；
    库不存在时才创建 + 灌样例数据。"""
    if os.path.exists(hd.DB_PATH):
        try:
            con = hd.get_connection(hd.DB_PATH, read_only=True)
            con.execute("SELECT 1 FROM datasets LIMIT 1")
            return con
        except Exception:
            pass
    return hd.ensure_catalog()


_con = _open_catalog()
_lock = threading.Lock()

_JSON_COLS = ["action_convention", "tasks", "scenes", "modalities",
              "linked_benchmarks", "quality_report"]


def _parse_row(d: dict) -> dict:
    """把 JSON 文本字段解析成对象，-1/0 之类空值规整一下。"""
    for c in _JSON_COLS:
        if c in d and isinstance(d[c], str) and d[c]:
            try:
                d[c] = json.loads(d[c])
            except Exception:
                pass
    for c in ("quality_score", "learnability_score"):
        if d.get(c) is not None and d[c] < 0:
            d[c] = None
    return d


@app.get("/api/stats")
def stats():
    with _lock:
        return hd.summary_stats(_con)


@app.get("/api/facets")
def facets():
    with _lock:
        return {
            "embodiments": hd.distinct_values(_con, "embodiment"),
            "formats": hd.distinct_values(_con, "source_format"),
            "provenances": hd.distinct_values(_con, "provenance_type"),
            "concepts": [{"id": cid, "label": lbl} for cid, lbl in tx.concept_options("tasks")],
        }


@app.get("/api/datasets")
def datasets(
    search: str = "", embodiment: str = "", format: str = "", provenance: str = "",
    commercial_only: bool = False, failures_only: bool = False,
    min_episodes: int = 0, min_quality: float = 0.0, concept: str = "",
):
    with _lock:
        df = hd.query_datasets(
            _con, search=search,
            embodiments=[embodiment] if embodiment else None,
            formats=[format] if format else None,
            provenances=[provenance] if provenance else None,
            commercial_only=commercial_only, failures_only=failures_only,
            min_episodes=min_episodes, min_quality=min_quality,
        )
        rows = [_parse_row(r) for r in df.to_dict(orient="records")]

        # 按任务概念过滤（优先读 concept_tags 表）
        if concept:
            try:
                ids = {r[0] for r in _con.execute(
                    "SELECT dataset_id FROM concept_tags WHERE category='tasks' AND concept_id=?",
                    [concept]).fetchall()}
                rows = [r for r in rows if r["dataset_id"] in ids]
            except Exception:
                rows = [r for r in rows
                        if concept in tx.align_many(r.get("tasks", []), "tasks")[0]]
    return {"count": len(rows), "datasets": rows}


@app.get("/api/datasets/{dataset_id:path}")
def dataset_detail(dataset_id: str):
    with _lock:
        df = _con.execute("SELECT * FROM datasets WHERE dataset_id = ?", [dataset_id]).df()
        if df.empty:
            return {"error": "not found"}
        row = _parse_row(df.to_dict(orient="records")[0])
        eps = hd.get_episodes(_con, dataset_id).to_dict(orient="records")
    return {"dataset": row, "episodes": eps}


@app.get("/api/coverage")
def coverage():
    """本体 × 任务概念 的覆盖度矩阵（用于前端热力图，一眼看 gap）。"""
    concepts = tx.concept_options("tasks")
    concept_ids = [cid for cid, _ in concepts]
    with _lock:
        embodiments = hd.distinct_values(_con, "embodiment")
        rows = _con.execute("SELECT dataset_id, embodiment, tasks FROM datasets").fetchall()
        # 优先用 concept_tags 表
        tag_map = {}
        try:
            for did, cid in _con.execute(
                    "SELECT dataset_id, concept_id FROM concept_tags WHERE category='tasks'").fetchall():
                tag_map.setdefault(did, set()).add(cid)
        except Exception:
            tag_map = None

    counts = {e: {c: 0 for c in concept_ids} for e in embodiments}
    for did, emb, tasks_json in rows:
        if tag_map is not None:
            cset = tag_map.get(did, set())
        else:
            try:
                raw = json.loads(tasks_json) if tasks_json else []
            except Exception:
                raw = []
            cset, _ = tx.align_many(raw, "tasks")
        for c in cset:
            if emb in counts and c in counts[emb]:
                counts[emb][c] += 1

    cells = [{"embodiment": e, "concept": c, "count": counts[e][c]}
             for e in embodiments for c in concept_ids]
    return {
        "embodiments": embodiments,
        "concepts": [{"id": cid, "label": lbl} for cid, lbl in concepts],
        "cells": cells,
    }


@app.get("/")
def root():
    return {"service": "RoboticDataHub API", "docs": "/docs"}
