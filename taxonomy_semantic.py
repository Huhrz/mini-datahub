"""
语义对齐（embedding）—— 按"意思"而非"字面"匹配
=================================================

解决规则版的天花板：'put the red cube into the box' 不含任何 pick_place 别名词，
字面对不上；但它"意思上"就是 pick_place。语义对齐用文本向量按意思相近来匹配，
大幅提升召回。

策略：先用规则版（精确别名，快又准），对不上的再用语义版兜底。

需要：pip install sentence-transformers（首次会下载一个多语言小模型，约几百 MB，
之后离线可用）。没装时自动退回纯规则版。
"""

import taxonomy as tx

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"   # 支持中英文
_model = None
_anchors = {}        # category -> [(concept_id, anchor_text), ...]
_anchor_emb = {}     # category -> np.ndarray (已归一化)


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def _build_anchors(category):
    if category in _anchor_emb:
        return
    import numpy as np
    items = []
    for c in tx.TAXONOMY[category]:
        for text in [c.en, c.zh, *c.aliases]:
            items.append((c.id, text))
    _anchors[category] = items
    embs = _load_model().encode([t for _, t in items], normalize_embeddings=True)
    _anchor_emb[category] = np.asarray(embs)


def semantic_align(raw, category, threshold=0.5):
    """按语义相似度对齐；返回 dict 或 None。"""
    _build_anchors(category)
    q = _load_model().encode([raw], normalize_embeddings=True)[0]
    sims = _anchor_emb[category] @ q          # 已归一化 -> 点积即余弦
    best = int(sims.argmax())
    score = float(sims[best])
    if score >= threshold:
        cid = _anchors[category][best][0]
        c = next(x for x in tx.TAXONOMY[category] if x.id == cid)
        return {"raw": raw, "concept_id": cid, "concept_en": c.en,
                "confidence": round(score, 2), "matched_by": "semantic"}
    return None


def align(raw, category, threshold=0.5):
    """组合对齐：先规则（精确/模糊），对不上再语义。语义不可用时安全退回。"""
    r = tx.align(raw, category)
    if r:
        return r
    try:
        return semantic_align(raw, category, threshold=threshold)
    except Exception:
        return None        # sentence-transformers 没装等情况 -> 退回规则结果(None)
