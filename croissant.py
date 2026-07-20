"""
Croissant 1.1 生成器（G5）—— 对外元数据 / 发现层
===================================================

对齐设计文档：对外用 **Croissant 1.1**（MLCommons 的 ML 数据集元数据标准，
schema.org 扩展）作发现层，自动获得 Google Dataset Search 等全球可发现性。

要点：
  - 联邦原则不变：Croissant 记录里的 distribution 指向**源**（HuggingFace 等），
    不 re-host 数据本体。
  - description 由**元数据模板拼**，不是 AI 生成（可复现、可追溯）。
  - 内部目录 schema 更丰富，Croissant 是"对外投影"：额外字段（本体/采集方式/
    质量分/taxonomy）挂在 schema.org 的 additionalProperty / keywords 上。

用法：
    import croissant
    jsonld = croissant.build_croissant(row)     # row = datasets 表一行(dict)
"""

import json

# Croissant 1.1 规范的标准 @context（MLCommons 官方词表）
CROISSANT_CONTEXT = {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "citeAs": "cr:citeAs",
    "column": "cr:column",
    "conformsTo": "dct:conformsTo",
    "cr": "http://mlcommons.org/croissant/",
    "data": {"@id": "cr:data", "@type": "@json"},
    "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
    "dct": "http://purl.org/dc/terms/",
    "examples": {"@id": "cr:examples", "@type": "@json"},
    "extract": "cr:extract",
    "field": "cr:field",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "format": "cr:format",
    "includes": "cr:includes",
    "isLiveDataset": "cr:isLiveDataset",
    "jsonPath": "cr:jsonPath",
    "key": "cr:key",
    "md5": "cr:md5",
    "parentField": "cr:parentField",
    "path": "cr:path",
    "recordSet": "cr:recordSet",
    "references": "cr:references",
    "regex": "cr:regex",
    "repeated": "cr:repeated",
    "replace": "cr:replace",
    "sc": "https://schema.org/",
    "separator": "cr:separator",
    "source": "cr:source",
    "subField": "cr:subField",
    "transform": "cr:transform",
}


def _as_list(v):
    """字段可能是 list 或 JSON 字符串，统一成 list。"""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            j = json.loads(v)
            return j if isinstance(j, list) else [v] if v.strip() else []
        except Exception:
            return [v] if v.strip() else []
    return []


def _spdx_url(spdx: str):
    if spdx and spdx not in ("unknown", ""):
        return f"https://spdx.org/licenses/{spdx}"
    return None


# 模态 -> schema.org / croissant 数据类型的粗映射
_MODALITY_TYPE = {
    "rgb": "sc:ImageObject",
    "depth": "sc:ImageObject",
    "state": "sc:Float",
    "action": "sc:Float",
    "language": "sc:Text",
}


def _description(row: dict, tasks, modalities) -> str:
    """纯模板拼装的事实性描述（非 AI 生成）。"""
    parts = []
    emb = row.get("embodiment") or "unknown"
    parts.append(f"Robot learning dataset. Embodiment: {emb}.")
    if row.get("robot_model"):
        parts.append(f"Robot: {row['robot_model']}.")
    if tasks:
        parts.append("Tasks: " + ", ".join(map(str, tasks[:10])) + ".")
    if modalities:
        parts.append("Modalities: " + ", ".join(map(str, modalities)) + ".")
    n_ep = int(row.get("n_episodes") or 0)
    n_fr = int(row.get("total_frames") or 0)
    fps = row.get("fps") or 0
    scale = []
    if n_ep:
        scale.append(f"{n_ep} episodes")
    if n_fr:
        scale.append(f"{n_fr} frames")
    if fps:
        scale.append(f"{fps} fps")
    if scale:
        parts.append("Scale: " + ", ".join(scale) + ".")
    parts.append(f"Canonical format: {row.get('source_format', 'unknown')}. "
                 f"Federated entry — data hosted at source ({row.get('source', 'source')}).")
    return " ".join(parts)


def build_croissant(row: dict) -> dict:
    """把一个目录项(dict) 变成合规的 Croissant 1.1 JSON-LD。"""
    tasks = _as_list(row.get("tasks"))
    scenes = _as_list(row.get("scenes"))
    modalities = _as_list(row.get("modalities"))
    dataset_id = row.get("dataset_id") or row.get("name") or "dataset"
    name = row.get("name") or dataset_id
    url = row.get("homepage") or row.get("source_uri") or ""
    src_uri = row.get("source_uri") or url

    keywords = ["robotics", "robot learning", "imitation learning", "manipulation"]
    keywords += [str(t) for t in tasks[:12]]
    if row.get("embodiment"):
        keywords.append(str(row["embodiment"]))
    keywords += [f"modality:{m}" for m in modalities]
    keywords = list(dict.fromkeys(keywords))          # 去重保序

    # 创建者：从 repo_id 前缀推组织（如 lerobot/pusht -> lerobot）
    org = dataset_id.split("/")[0] if "/" in str(dataset_id) else row.get("source", "")

    doc = {
        "@context": CROISSANT_CONTEXT,
        "@type": "sc:Dataset",
        "dct:conformsTo": "http://mlcommons.org/croissant/1.1",
        "@id": url or dataset_id,
        "name": name,
        "description": _description(row, tasks, modalities),
        "keywords": keywords,
        "isLiveDataset": True,          # 联邦：指向源，可能随源更新
    }
    if url:
        doc["url"] = url
    if org:
        doc["creator"] = {"@type": "sc:Organization", "name": org}
    lic = _spdx_url(row.get("license_spdx"))
    if lic:
        doc["license"] = lic

    # distribution：联邦指针，指向源（不 re-host）
    fmt = str(row.get("source_format", ""))
    enc = ("application/x-parquet" if "lerobot" in fmt else
           "application/x-hdf5" if "hdf5" in fmt else
           "application/octet-stream")
    if src_uri:
        doc["distribution"] = [{
            "@type": "cr:FileObject",
            "@id": "source-repository",
            "name": "source-repository",
            "description": f"Federated pointer to the source dataset ({row.get('source', '')}). "
                           f"Data is not re-hosted by this catalog.",
            "contentUrl": src_uri,
            "encodingFormat": enc,
            "sha256": "",           # 联邦不转存，不承诺内容哈希
        }]

    # recordSet：把模态描述成字段（下游 ML 工具可读）
    fields = []
    for m in modalities:
        fields.append({
            "@type": "cr:Field",
            "@id": f"features/{m}",
            "name": str(m),
            "description": f"{m} stream",
            "dataType": _MODALITY_TYPE.get(str(m), "sc:Text"),
        })
    if fields:
        doc["recordSet"] = [{
            "@type": "cr:RecordSet",
            "@id": "episodes",
            "name": "episodes",
            "description": "Per-episode multi-modal robot trajectories (fields point to source).",
            "field": fields,
        }]

    # 额外内部元数据 -> schema.org additionalProperty（不丢失、但明确是扩展）
    extra = []

    def _prop(k, v):
        if v not in (None, "", "unknown", -1):
            extra.append({"@type": "sc:PropertyValue", "name": k, "value": v})

    _prop("embodiment", row.get("embodiment"))
    _prop("provenance_type", row.get("provenance_type"))
    _prop("dof", row.get("dof"))
    _prop("fps", row.get("fps"))
    _prop("n_episodes", row.get("n_episodes"))
    _prop("n_cameras", row.get("n_cameras"))
    _prop("commercial_ok", bool(row.get("commercial_ok")))
    _prop("source_format", row.get("source_format"))
    if row.get("quality_score") is not None and (row.get("quality_score") or -1) >= 0:
        qtier = ""
        try:
            qr = row.get("quality_report")
            qr = json.loads(qr) if isinstance(qr, str) else (qr or {})
            qtier = qr.get("tier", "")
        except Exception:
            pass
        _prop("quality_score" + (f" ({qtier})" if qtier else ""), row.get("quality_score"))
    for c in tasks:
        extra.append({"@type": "sc:PropertyValue", "name": "task_concept", "value": str(c)})
    for s in scenes:
        extra.append({"@type": "sc:PropertyValue", "name": "scene", "value": str(s)})
    if extra:
        doc["additionalProperty"] = extra

    return doc


def to_json(row: dict, indent=2) -> str:
    return json.dumps(build_croissant(row), ensure_ascii=False, indent=indent)
