"""
语义向量：增量计算 + 共享逻辑
==============================

核心思想（回应"大规模不现实"的顾虑）：
  - 粒度是"每个数据集一个向量"（不是每条轨迹），几万个也才几十 MB；
  - **增量**：只给 dataset_embeddings 里还没有的数据集算，算过的跳过；
  - 接入新数据时自动补算（见 09/11），永不全量重跑。

需要 sentence-transformers 才会真的算向量；没装则安全跳过（不报错、不阻塞接入）。
真到千万级（如轨迹级检索）时，把这里的存储换成 LanceDB 即可，接口不变。
"""

import json
import store

_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"   # 多语言，支持中英文跨语言检索
_model = None


def dataset_text(name, tasks_json):
    """把数据集的名称+任务描述拼成一段代表'它在做什么'的文本。"""
    try:
        tasks = json.loads(tasks_json) if tasks_json else []
    except Exception:
        tasks = []
    return (str(name) + "。 " + "; ".join(str(t) for t in tasks[:20])).strip()


def ensure_table(con):
    store.run(con, "CREATE TABLE IF NOT EXISTS dataset_embeddings "
                   "(dataset_id VARCHAR PRIMARY KEY, embedding VARCHAR)")


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_missing(con, force=False, quiet=False):
    """
    给缺向量的数据集增量计算并写入 dataset_embeddings；force=True 则全量重算。
    返回本次新算的条数。没装 sentence-transformers 时安全跳过（返回 0）。
    """
    ensure_table(con)
    if force:
        store.run(con, "DELETE FROM dataset_embeddings")
        rows = store.run(con, "SELECT dataset_id, name, tasks FROM datasets")
    else:
        rows = store.run(con,
            "SELECT d.dataset_id, d.name, d.tasks FROM datasets d "
            "LEFT JOIN dataset_embeddings e ON d.dataset_id = e.dataset_id "
            "WHERE e.dataset_id IS NULL")

    if not rows:
        if not quiet:
            print("[embeddings] 无需新算：所有数据集都已有向量。")
        return 0

    try:
        model = _get_model()
    except Exception as e:
        if not quiet:
            print(f"[embeddings] 无法加载向量模型，跳过。真实原因：{type(e).__name__}: {str(e)[:300]}")
        return 0

    import numpy as np
    texts = [dataset_text(n, t) for _, n, t in rows]
    if not quiet:
        print(f"[embeddings] 增量计算 {len(rows)} 个数据集的向量…")
    embs = np.asarray(model.encode(texts, normalize_embeddings=True,
                                   batch_size=256, show_progress_bar=not quiet))
    store.run_many(con,
        "INSERT INTO dataset_embeddings VALUES (?, ?)",
        [(rid, json.dumps([round(float(x), 5) for x in vec]))
         for (rid, _, _), vec in zip(rows, embs)])
    if not quiet:
        print(f"[embeddings] 已写入 {len(rows)} 条新向量。")
    return len(rows)


def assign_concepts(con, extra_threshold=0.42, quiet=False):
    """
    用语义向量把每个数据集分到"最接近的任务概念"（覆盖度地图靠这张表）。
    每个数据集至少分到最相近的一个概念(argmax)，另加所有相似度超过阈值的概念。
    这样覆盖度地图不再大面积空白，而且分配靠"意思"而非字面。
    需要 dataset_embeddings（先跑 embed_missing）和 sentence-transformers。
    """
    import numpy as np
    import taxonomy as tx

    ensure_table(con)
    rows = store.run(con, "SELECT dataset_id, embedding FROM dataset_embeddings")
    if not rows:
        if not quiet:
            print("[concepts] 没有数据集向量，先跑 13_build_embeddings.py。")
        return 0
    try:
        model = _get_model()
    except Exception:
        if not quiet:
            print("[concepts] 未装 sentence-transformers，跳过语义打标。")
        return 0

    ids = [r[0] for r in rows]
    mat = np.asarray([json.loads(r[1]) for r in rows], dtype="float32")   # (N, d)

    concepts = tx.TAXONOMY["tasks"]
    ctexts = [f"{c.zh} {c.en} " + " ".join(c.aliases) for c in concepts]
    cvec = np.asarray(model.encode(ctexts, normalize_embeddings=True), dtype="float32")  # (K, d)
    sims = mat @ cvec.T                                                    # (N, K)

    store.run(con, "CREATE TABLE IF NOT EXISTS concept_tags "
                   "(dataset_id VARCHAR, category VARCHAR, concept_id VARCHAR)")
    store.run(con, "DELETE FROM concept_tags WHERE category = 'tasks'")

    total = 0
    for i, did in enumerate(ids):
        srow = sims[i]
        chosen = {concepts[int(srow.argmax())].id}          # 最近概念，人人有份
        for k in range(len(concepts)):
            if srow[k] >= extra_threshold:
                chosen.add(concepts[k].id)
        for cid in chosen:
            store.run(con, "INSERT INTO concept_tags VALUES (?, 'tasks', ?)", [did, cid])
            total += 1
    if not quiet:
        print(f"[concepts] 语义打标完成：{len(ids)} 个数据集 → {total} 个概念标签。")
    return total
