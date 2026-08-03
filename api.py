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

from fastapi import FastAPI, Query, Header, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

import hub_data as hd
import taxonomy as tx
import store
import accounts

app = FastAPI(title="RoboticDataHub API", version="0.1.0")

# 允许前端（localhost:5173 等）跨域访问
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["*"], allow_headers=["*"],
)


def _open_catalog():
    """打开目录连接。Postgres 天生支持并发读写；DuckDB 则优先只读打开
    （不占写锁，减少和摄入进程抢锁）。库不存在时创建 + 灌样例数据。"""
    if store.is_pg() or os.path.exists(hd.DB_PATH):
        try:
            con = store.connect(read_only=not store.is_pg())
            store.run(con, "SELECT 1 FROM datasets LIMIT 1")
            return con
        except Exception:
            pass
    return hd.ensure_catalog()


_con = _open_catalog()
_lock = threading.Lock()

# 账户功能所需的表（用户/会话/收藏集）。Postgres 下可写；DuckDB 只读时会跳过。
try:
    with _lock:
        accounts.ensure_tables(_con)
except Exception as e:
    print(f"[accounts] 建表跳过（DuckDB 只读或其它）：{repr(e)[:80]}")


def _bearer(authorization: str) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return (authorization or "").strip()


def current_user(authorization: str = Header(default="")):
    """从 Authorization: Bearer <token> 解析登录用户；未登录返回 None。"""
    token = _bearer(authorization)
    if not token:
        return None
    with _lock:
        return accounts.user_for_token(_con, token)

_JSON_COLS = ["action_convention", "tasks", "scenes", "modalities",
              "linked_benchmarks", "quality_report"]


def _clean_json(v):
    """把 NaN / Infinity 换成 None —— 它们不是合法 JSON，会让整个响应序列化失败。
    （numpy/pandas 读出来的空值常是 NaN，必须在出口统一清洗。）"""
    import math
    if isinstance(v, float):
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(v, dict):
        return {k: _clean_json(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_clean_json(x) for x in v]
    return v


def _parse_row(d: dict) -> dict:
    """把 JSON 文本字段解析成对象，-1/0 之类空值规整一下，并清洗 NaN/Inf。"""
    for c in _JSON_COLS:
        if c in d and isinstance(d[c], str) and d[c]:
            try:
                d[c] = json.loads(d[c])
            except Exception:
                pass
    for c in ("quality_score", "learnability_score"):
        try:
            if d.get(c) is not None and d[c] < 0:
                d[c] = None
        except TypeError:
            pass
    return {k: _clean_json(v) for k, v in d.items()}


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


def _link_health_map():
    """dataset_id -> alive(bool)。没有 link_health 表时返回空 dict。"""
    try:
        return {r[0]: bool(r[1]) for r in store.run(_con, "SELECT dataset_id, alive FROM link_health")}
    except Exception:
        return {}


@app.get("/api/datasets")
def datasets(
    search: str = "", embodiment: str = "", format: str = "", provenance: str = "",
    commercial_only: bool = False, failures_only: bool = False,
    min_episodes: int = 0, min_quality: float = 0.0, concept: str = "",
    page: int = 1, page_size: int = 20,
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

        # 按任务概念过滤：concept 支持多选（逗号分隔），命中任一即保留
        concepts = [c for c in (concept or "").split(",") if c.strip()]
        if concepts:
            try:
                placeholders = ",".join(["?"] * len(concepts))
                ids = {r[0] for r in store.run(_con,
                    f"SELECT dataset_id FROM concept_tags WHERE category='tasks' "
                    f"AND concept_id IN ({placeholders})", concepts)}
                rows = [r for r in rows if r["dataset_id"] in ids]
            except Exception:
                rows = [r for r in rows
                        if set(concepts) & tx.align_many(r.get("tasks", []), "tasks")[0]]

        total = len(rows)
        # 服务端分页：大列表不一次性返回，前端不卡
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        start = (page - 1) * page_size
        page_rows = rows[start:start + page_size]

        # 附加链接存活状态（失效链接前端标红）
        health = _link_health_map()
        for r in page_rows:
            r["link_alive"] = health.get(r["dataset_id"])   # True/False/None(未检查)

    return {"count": total, "page": page, "page_size": page_size,
            "pages": (total + page_size - 1) // page_size, "datasets": page_rows}


@app.get("/api/export")
def export_manifest(ids: str = "", commercial_only: bool = False):
    """训练清单导出（G3）+ License 门禁（设计原则5）：给一组数据集，产出可复现的
    data-mixture 清单（指向源，不搬数据）。按 license 自动放行/拦截并给出警示。
    commercial_only=true 时，直接把非商用数据集从清单里剔除（硬门禁）。"""
    id_list = [x for x in ids.split(",") if x.strip()]
    if not id_list:
        return {"error": "no ids"}
    with _lock:
        ph = ",".join(["?"] * len(id_list))
        df = store.run_df(_con,
            f"SELECT dataset_id, name, source, source_uri, source_format, license_spdx, "
            f"commercial_ok, redistribute_ok, embodiment, n_episodes, quality_score FROM datasets "
            f"WHERE dataset_id IN ({ph})", id_list)
    items = [_clean_json(r) for r in df.to_dict(orient="records")]
    for i in items:
        i["commercial_ok"] = bool(i.get("commercial_ok"))
        i["redistribute_ok"] = bool(i.get("redistribute_ok"))

    blocked = []
    included = []
    for i in items:
        if commercial_only and not i["commercial_ok"]:
            blocked.append(i["dataset_id"])          # 硬门禁：剔除
        else:
            included.append(i)

    non_comm = [i["dataset_id"] for i in included if not i["commercial_ok"]]
    non_redist = [i["dataset_id"] for i in included if not i["redistribute_ok"]]
    warnings = []
    if non_comm:
        warnings.append(f"{len(non_comm)} 个数据集为非商用许可，请勿用于商业训练。")
    if non_redist:
        warnings.append(f"{len(non_redist)} 个数据集不可再分发，仅可按源许可就地使用。")
    if blocked:
        warnings.append(f"已按 commercial_only 门禁剔除 {len(blocked)} 个非商用数据集。")

    return {
        "manifest_version": "1.1",
        "note": "联邦训练清单：指向数据源，不含数据本体。weight 可自行调整。",
        "n_datasets": len(included),
        "total_episodes": int(sum(int(i.get("n_episodes") or 0) for i in included)),
        "license_gating": {
            "commercial_only": commercial_only,
            "blocked": blocked,
            "non_commercial": non_comm,
            "non_redistributable": non_redist,
            "warnings": warnings,
        },
        "datasets": [{**i, "weight": 1.0} for i in included],
    }


@app.get("/api/croissant/{dataset_id:path}")
def croissant_record(dataset_id: str):
    """Croissant 1.1 元数据（G5）：对外发现层，可提交 Google Dataset Search。
    联邦：distribution 指向源，不 re-host。返回 application/ld+json。"""
    from fastapi.responses import JSONResponse
    import croissant as cr
    with _lock:
        df = store.run_df(_con, "SELECT * FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return JSONResponse({"error": "not found"}, status_code=404)
    row = _parse_row(df.to_dict(orient="records")[0])
    return JSONResponse(cr.build_croissant(row),
                        media_type="application/ld+json; charset=utf-8")


def _fmt_of(row: dict) -> str:
    """归一到播放器认识的格式：'lerobot' / 'hdf5' / ''（暂不支持）。"""
    sf = str(row.get("source_format", ""))
    if row.get("source") == "huggingface" or "lerobot" in sf:
        return "lerobot"
    if "hdf5" in sf or "h5" in sf:
        return "hdf5"
    return ""


# ---------------- 样本缓存（预计算 + 持久化）----------------
# 上万条轨迹不全量拉。每个数据集只在首次接触时解析一小撮"代表性样本"的片段坐标，
# 存到磁盘 JSON（避开 DuckDB 只读连接的写锁问题）。之后浏览只读缓存，秒开、不再打 HF。
_PREVIEW_CACHE_PATH = os.path.abspath("viz_previews.json")
_cache_lock = threading.Lock()
_preview_cache = {}


def _load_preview_cache():
    global _preview_cache
    try:
        with open(_PREVIEW_CACHE_PATH) as f:
            _preview_cache = json.load(f)
    except Exception:
        _preview_cache = {}


def _save_preview_cache():
    try:
        with open(_PREVIEW_CACHE_PATH, "w") as f:
            json.dump(_preview_cache, f)
    except Exception:
        pass


_load_preview_cache()


def _compute_samples(dataset_id: str) -> dict:
    with _lock:
        df = store.run_df(_con, "SELECT source, source_format, source_uri FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return {"thumbnail": "", "samples": []}
    row = df.to_dict(orient="records")[0]
    fmt = _fmt_of(row)
    import episode as ep_mod
    if fmt == "lerobot":
        return ep_mod.samples(dataset_id)
    if fmt == "hdf5":
        return ep_mod.hdf5_samples(dataset_id, row.get("source_uri"))
    return {"thumbnail": "", "samples": []}


def _get_samples(dataset_id: str, force: bool = False) -> dict:
    if not force:
        with _cache_lock:
            if dataset_id in _preview_cache:
                return _preview_cache[dataset_id]
    try:
        data = _compute_samples(dataset_id)
    except Exception:
        data = {"thumbnail": "", "samples": []}
    with _cache_lock:
        _preview_cache[dataset_id] = data
        _save_preview_cache()
    return data


@app.get("/api/samples/{dataset_id:path}")
def samples(dataset_id: str, refresh: int = 0):
    """详情页用：~10 条代表性样本的片段坐标（缩略图 + 每条 cameras/clip）。缓存到磁盘。"""
    return {"dataset_id": dataset_id, **_get_samples(dataset_id, force=bool(refresh))}


@app.get("/api/preview/{dataset_id:path}")
def preview(dataset_id: str):
    """卡片缩略图：极轻路径 —— 只读 info.json 拼首个视频文件 URL（不碰 meta/episodes /
    httpfs / 大文件）。这样 v3.0 封面也能稳定出图。"""
    with _lock:
        df = store.run_df(_con, "SELECT source, source_format, source_uri FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return {}
    row = df.to_dict(orient="records")[0]
    fmt = _fmt_of(row)
    try:
        import episode as ep_mod
        if fmt == "lerobot":
            return ep_mod.preview(dataset_id)
        if fmt == "hdf5":
            return ep_mod.hdf5_preview(dataset_id, row.get("source_uri"))
    except Exception:
        return {}
    return {}


@app.get("/api/episode/{dataset_id:path}")
def episode(dataset_id: str, ep: int = 0):
    """自建播放器数据：相机视频 + 状态/动作曲线 + fps（替代 HF 的 iframe 页面）。"""
    with _lock:
        df = store.run_df(_con, "SELECT source, source_format, source_uri, homepage FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return {"playable": False, "reason": "not found"}
    row = df.to_dict(orient="records")[0]
    fmt = _fmt_of(row)
    if not fmt:
        return {"playable": False,
                "reason": "自建播放器目前支持 LeRobot/HF 与 HDF5 格式，其它来源将逐步适配。",
                "homepage": row.get("homepage")}
    try:
        import episode as ep_mod
        if fmt == "lerobot":
            return ep_mod.lerobot_episode(dataset_id, int(ep))
        return ep_mod.hdf5_episode(dataset_id, row.get("source_uri"), int(ep))
    except Exception as e:
        return {"playable": False, "reason": f"提取失败：{type(e).__name__}: {e}",
                "homepage": row.get("homepage")}


@app.get("/api/hdf5_video/{dataset_id:path}")
def hdf5_video(dataset_id: str, cam: str, thumb: int = 0):
    """把 HDF5 里某路相机转码成 mp4 并回传（缓存）。cam 是文件内数据集路径；
    source_uri 从库里取（不信任客户端传的本地路径），只服务已入库数据集自己的 h5。"""
    from fastapi.responses import FileResponse, JSONResponse
    with _lock:
        df = store.run_df(_con, "SELECT source_uri, source_format FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return JSONResponse({"error": "not found"}, status_code=404)
    row = df.to_dict(orient="records")[0]
    if _fmt_of(row) != "hdf5":
        return JSONResponse({"error": "not hdf5"}, status_code=400)
    try:
        import episode as ep_mod
        mp4 = ep_mod.hdf5_video_file(row.get("source_uri"), cam, thumb=bool(thumb))
        return FileResponse(mp4, media_type="video/mp4")
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@app.get("/api/datasets/{dataset_id:path}")
def dataset_detail(dataset_id: str):
    with _lock:
        df = store.run_df(_con, "SELECT * FROM datasets WHERE dataset_id = ?", [dataset_id])
        if df.empty:
            return {"error": "not found"}
        row = _parse_row(df.to_dict(orient="records")[0])
        eps = hd.get_episodes(_con, dataset_id).to_dict(orient="records")
    return {"dataset": row, "episodes": eps}


def _coverage_counts():
    """本体 × 任务概念 的计数矩阵。返回 (embodiments, concepts[(id,label)], counts[e][c])。"""
    concepts = tx.concept_options("tasks")
    concept_ids = [cid for cid, _ in concepts]
    with _lock:
        embodiments = hd.distinct_values(_con, "embodiment")
        rows = store.run(_con, "SELECT dataset_id, embodiment, tasks FROM datasets")
        tag_map = {}
        try:
            for did, cid in store.run(_con,
                    "SELECT dataset_id, concept_id FROM concept_tags WHERE category='tasks'"):
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
    return embodiments, concepts, counts


@app.get("/api/coverage")
def coverage():
    """本体 × 任务概念 的覆盖度矩阵（用于前端热力图，一眼看 gap）。"""
    embodiments, concepts, counts = _coverage_counts()
    concept_ids = [cid for cid, _ in concepts]
    cells = [{"embodiment": e, "concept": c, "count": counts[e][c]}
             for e in embodiments for c in concept_ids]
    return {
        "embodiments": embodiments,
        "concepts": [{"id": cid, "label": lbl} for cid, lbl in concepts],
        "cells": cells,
    }


@app.get("/api/gaps")
def gaps():
    """数据缺口报告：哪些 本体×任务概念 组合全球都缺（count=0），以及全局最稀缺的概念。
    复用覆盖度矩阵，指导'该采什么数据'——数据 hub 的独有价值。"""
    embodiments, concepts, counts = _coverage_counts()
    concept_ids = [cid for cid, _ in concepts]
    labels = {cid: lbl for cid, lbl in concepts}
    total = len(embodiments) * len(concept_ids)
    covered = sum(1 for e in embodiments for c in concept_ids if counts[e][c] > 0)
    empty = [{"embodiment": e, "concept": c, "concept_label": labels[c]}
             for e in embodiments for c in concept_ids if counts[e][c] == 0]
    # 全局最稀缺的任务概念（按总数升序）
    concept_totals = sorted(
        ({"concept": c, "label": labels[c],
          "total": sum(counts[e][c] for e in embodiments)} for c in concept_ids),
        key=lambda x: x["total"])
    # 各本体覆盖了多少概念
    emb_coverage = [{"embodiment": e,
                     "covered": sum(1 for c in concept_ids if counts[e][c] > 0),
                     "of": len(concept_ids)} for e in embodiments]
    return {
        "total_cells": total, "covered": covered,
        "coverage_pct": round(100 * covered / total, 1) if total else 0,
        "gap_count": len(empty), "gaps": empty,
        "scarcest_concepts": concept_totals[:10],
        "embodiment_coverage": emb_coverage,
    }


# ---------------- 语义搜索（跨语言）----------------
_emb = {"ids": None, "mat": None, "model": None}


def _load_embeddings():
    import numpy as np
    try:
        rows = store.run(_con, "SELECT dataset_id, embedding FROM dataset_embeddings")
    except Exception:
        return False
    if not rows:
        return False
    _emb["ids"] = [r[0] for r in rows]
    _emb["mat"] = np.asarray([json.loads(r[1]) for r in rows], dtype="float32")
    return True


@app.get("/api/similar/{dataset_id:path}")
def similar(dataset_id: str, k: int = 6):
    """相似数据集推荐：复用语义向量做最近邻（向量已归一化，点积=余弦相似度）。"""
    import numpy as np
    if _emb["ids"] is None:
        _load_embeddings()
    if not _emb["ids"] or dataset_id not in _emb["ids"]:
        return {"dataset_id": dataset_id, "similar": []}
    idx = _emb["ids"].index(dataset_id)
    sims = _emb["mat"] @ _emb["mat"][idx]
    order = np.argsort(-sims)
    ids, score = [], {}
    for i in order:
        did = _emb["ids"][int(i)]
        if did == dataset_id:
            continue
        ids.append(did)
        score[did] = float(sims[int(i)])
        if len(ids) >= max(1, min(k, 20)):
            break
    if not ids:
        return {"dataset_id": dataset_id, "similar": []}
    with _lock:
        ph = ",".join(["?"] * len(ids))
        df = store.run_df(_con,
            f"SELECT dataset_id, name, embodiment, source_format, n_episodes, "
            f"quality_score, commercial_ok FROM datasets WHERE dataset_id IN ({ph})", ids)
    byid = {r["dataset_id"]: r for r in df.to_dict(orient="records")}
    out = [_clean_json({**byid[d], "score": round(score[d], 3)}) for d in ids if d in byid]
    return {"dataset_id": dataset_id, "similar": out}


import functools as _functools


@_functools.lru_cache(maxsize=512)
def _hf_repo_exists(repo: str) -> bool:
    try:
        from huggingface_hub import dataset_info
        dataset_info(repo)        # 走 HF_ENDPOINT 镜像（服务器已配）
        return True
    except Exception:
        return False


@app.get("/api/oxe_hf/{dataset_id:path}")
def oxe_hf_conversion(dataset_id: str):
    """OXE 数据集 → HF LeRobot 转换版映射（可视化用）。核验存在后才返回 repo。"""
    with _lock:
        df = store.run_df(_con, "SELECT source FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty or df.to_dict(orient="records")[0].get("source") != "openx":
        return {"repo": None}
    import oxe_registry as R
    name = dataset_id.split("/")[-1]
    guess = R.hf_conversion_guess(name)
    return {"repo": guess if _hf_repo_exists(guess) else None, "guess": guess}


@app.get("/api/benchmarks/{dataset_id:path}")
def benchmarks_for(dataset_id: str):
    """评测出口链接（G4）：按本体 + 任务概念，推荐适用的公开评测基准并回链榜单页。"""
    import benchmarks as bm
    with _lock:
        df = store.run_df(_con, "SELECT embodiment, source FROM datasets WHERE dataset_id = ?", [dataset_id])
        if df.empty:
            return {"dataset_id": dataset_id, "benchmarks": []}
        row = df.to_dict(orient="records")[0]
        try:
            concepts = [r[0] for r in store.run(_con,
                "SELECT concept_id FROM concept_tags WHERE dataset_id = ? AND category='tasks'", [dataset_id])]
        except Exception:
            concepts = []
    return {"dataset_id": dataset_id,
            "benchmarks": bm.match(row.get("embodiment", ""), concepts, dataset_id, row.get("source", ""))}


# ==================== 学生引导（术语释义 + 学习路径）====================
@app.get("/api/glossary")
def glossary_all():
    """术语词典：前端悬停讲解用。"""
    import glossary as gl
    return {"terms": gl.all_terms()}


@app.get("/api/learning_path")
def learning_path():
    """入门学习路径：每步挂上目录里真实的示例数据集。"""
    import learning_path as lp
    with _lock:
        df = store.run_df(_con,
            "SELECT dataset_id, name, embodiment, source_format, n_episodes, n_cameras, "
            "commercial_ok, modalities, action_convention FROM datasets ORDER BY n_episodes")
    rows = [_parse_row(r) for r in df.to_dict(orient="records")]
    return {"steps": lp.build(rows)}


# ==================== 缓存截图（快速按图浏览）====================
def _dataset_video_url(dataset_id: str):
    with _lock:
        df = store.run_df(_con, "SELECT source, source_format FROM datasets WHERE dataset_id = ?", [dataset_id])
    if df.empty:
        return None
    row = df.to_dict(orient="records")[0]
    if _fmt_of(row) == "lerobot":
        try:
            import episode
            info = episode._info(dataset_id)
            return episode._first_video_url(dataset_id, info)
        except Exception:
            return None
    return None


@app.get("/api/thumbs/{dataset_id:path}")
def thumbs_list(dataset_id: str, make: int = 0):
    """返回该数据集已缓存的截图 URL 列表。make=1 时若无缓存则现抽（详情页用，画廊用 0 只读缓存）。"""
    import thumbs
    if make and not thumbs.has_cache(dataset_id):
        url = _dataset_video_url(dataset_id)
        if url:
            thumbs.extract(dataset_id, url)
    files = thumbs.cached_files(dataset_id)
    return {"count": len(files), "urls": [f"/api/thumb/{dataset_id}?i={i}" for i in range(len(files))]}


@app.get("/api/thumb/{dataset_id:path}")
def thumb_img(dataset_id: str, i: int = 0):
    """回传第 i 张缓存截图（本地 JPEG，秒开）。"""
    import thumbs
    files = thumbs.cached_files(dataset_id)
    if not files or i < 0 or i >= len(files):
        return JSONResponse({"error": "no thumb"}, status_code=404)
    return FileResponse(files[i], media_type="image/jpeg")


# ==================== 问卷收集与自动统计 ====================
import survey as _survey

try:
    with _lock:
        _survey.ensure_tables(_con)
except Exception as e:
    print(f"[survey] 建表跳过：{repr(e)[:80]}")

_ADMINS = [u.strip() for u in os.environ.get("MDH_ADMIN_USERS", "").split(",") if u.strip()]


def _can_view_survey(user):
    """未配置 MDH_ADMIN_USERS 时，任何已登录用户可看；配置了则仅限名单内。"""
    if not user:
        return False
    return (not _ADMINS) or (user in _ADMINS)


@app.post("/api/survey/submit")
def survey_submit(body: dict):
    """问卷提交（公开，无需登录）。"""
    answers = body.get("answers") or body
    if not isinstance(answers, dict) or not answers:
        return JSONResponse({"error": "empty"}, status_code=400)
    try:
        with _lock:
            rid = _survey.submit(_con, answers)
        return {"ok": True, "id": rid}
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@app.get("/api/survey/summary")
def survey_summary(user=Depends(current_user)):
    """自动聚合统计（需登录）。"""
    if not _can_view_survey(user):
        return JSONResponse({"error": "需要登录后查看"}, status_code=401)
    with _lock:
        return _survey.summarize(_con)


@app.get("/api/survey/export")
def survey_export(user=Depends(current_user)):
    """导出全部原始回答（需登录）。"""
    if not _can_view_survey(user):
        return JSONResponse({"error": "需要登录后查看"}, status_code=401)
    with _lock:
        return {"rows": _survey.export_rows(_con)}


# ==================== 账户 + 收藏集（MVP demo）====================
@app.post("/api/auth/register")
def auth_register(body: dict):
    with _lock:
        u, err = accounts.register(_con, body.get("username"), body.get("password"))
        if err:
            return JSONResponse({"error": err}, status_code=400)
        token, _ = accounts.login(_con, body.get("username"), body.get("password"))
    return {"username": u, "token": token}


@app.post("/api/auth/login")
def auth_login(body: dict):
    with _lock:
        token, err = accounts.login(_con, body.get("username"), body.get("password"))
    if err:
        return JSONResponse({"error": err}, status_code=401)
    return {"username": body.get("username"), "token": token}


@app.post("/api/auth/logout")
def auth_logout(authorization: str = Header(default="")):
    with _lock:
        accounts.logout(_con, _bearer(authorization))
    return {"ok": True}


@app.get("/api/auth/me")
def auth_me(user=Depends(current_user)):
    return {"username": user}


@app.get("/api/collections")
def collections_list(user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)
    with _lock:
        return {"collections": accounts.list_collections(_con, user)}


@app.post("/api/collections")
def collections_create(body: dict, user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)
    with _lock:
        cid = accounts.create_collection(_con, user, body.get("name"), body.get("ids") or [])
    return {"id": cid}


@app.get("/api/collections/{cid}")
def collections_get(cid: str, user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)
    with _lock:
        ids = accounts.collection_ids(_con, cid, user)
        if ids is None:
            return JSONResponse({"error": "not found"}, status_code=404)
        rows = []
        if ids:
            ph = ",".join(["?"] * len(ids))
            df = store.run_df(_con,
                f"SELECT dataset_id, name, embodiment, source_format, n_episodes, "
                f"quality_score, commercial_ok FROM datasets WHERE dataset_id IN ({ph})", ids)
            rows = [_clean_json(r) for r in df.to_dict(orient="records")]
    return {"id": cid, "ids": ids, "datasets": rows}


@app.delete("/api/collections/{cid}")
def collections_delete(cid: str, user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)
    with _lock:
        ok = accounts.delete_collection(_con, cid, user)
    return {"ok": ok}


@app.get("/api/search")
def search(q: str = "", limit: int = 60):
    """搜索框专用：有向量表则做跨语言语义排序，否则退回关键词搜索。"""
    q = (q or "").strip()
    if not q:
        return {"count": 0, "datasets": [], "mode": "empty"}

    # 尝试语义搜索
    try:
        import numpy as np
        if _emb["ids"] is None:
            _load_embeddings()
        if _emb["ids"]:
            if _emb["model"] is None:
                from sentence_transformers import SentenceTransformer
                _emb["model"] = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            qv = np.asarray(_emb["model"].encode([q], normalize_embeddings=True)[0], dtype="float32")
            sims = _emb["mat"] @ qv
            order = list(np.argsort(-sims)[:limit])
            ids = [_emb["ids"][i] for i in order]
            score = {_emb["ids"][i]: float(sims[i]) for i in order}
            with _lock:
                df = store.run_df(_con,
                    f"SELECT * FROM datasets WHERE dataset_id IN ({','.join(['?']*len(ids))})", ids)
            byid = {r["dataset_id"]: _parse_row(r) for r in df.to_dict(orient="records")}
            out = []
            for did in ids:
                if did in byid and score[did] > 0.15:   # 太不相关的丢弃
                    row = byid[did]
                    row["score"] = round(score[did], 3)
                    out.append(row)
            return {"count": len(out), "datasets": out, "mode": "semantic"}
    except Exception:
        pass

    # 退回关键词搜索
    with _lock:
        df = hd.query_datasets(_con, search=q)
    rows = [_parse_row(r) for r in df.to_dict(orient="records")]
    return {"count": len(rows), "datasets": rows, "mode": "keyword"}


@app.get("/")
def root():
    return {"service": "RoboticDataHub API", "docs": "/docs"}
