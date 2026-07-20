"""
批量导出 Croissant 元数据（G5）—— 供对外托管 / 提交 Google Dataset Search
============================================================================

给目录里每个数据集生成一份 Croissant 1.1 JSON-LD，落盘到 croissant/ 目录。
再配一份 sitemap 风格的 index.json，方便对外托管后让爬虫发现。

用法：
    python 14_export_croissant.py                 # 导出全部
    python 14_export_croissant.py --out croissant # 指定输出目录

说明：Google Dataset Search 通过网页里嵌的 schema.org/Dataset JSON-LD 抓取。
真正提交时，需要把这些 JSON-LD 嵌进各数据集的可爬取网页（或托管为静态页 + sitemap）。
本脚本先把合规记录产出来，托管方式按部署再定。
"""

import os
import re
import json
import argparse

import store
import croissant as cr


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(name)).strip("_") or "dataset"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="croissant", help="输出目录")
    args = ap.parse_args()

    con = store.connect(read_only=not store.is_pg())
    rows = store.run_df(con, "SELECT * FROM datasets ORDER BY name").to_dict(orient="records")
    store.close(con)
    if not rows:
        print("[提示] 目录为空，请先接入数据。")
        return

    os.makedirs(args.out, exist_ok=True)
    index = []
    for r in rows:
        # JSON 文本字段解析回对象
        for c in ("tasks", "scenes", "modalities", "quality_report", "action_convention"):
            v = r.get(c)
            if isinstance(v, str) and v:
                try:
                    r[c] = json.loads(v)
                except Exception:
                    pass
        doc = cr.build_croissant(r)
        fname = _safe(r["dataset_id"]) + ".jsonld"
        with open(os.path.join(args.out, fname), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        index.append({"dataset_id": r["dataset_id"], "name": r.get("name"),
                      "file": fname, "url": r.get("homepage") or r.get("source_uri")})

    with open(os.path.join(args.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(index), "records": index}, f, ensure_ascii=False, indent=2)

    print(f"[ok] 已导出 {len(index)} 份 Croissant 记录到 {args.out}/ （含 index.json）")


if __name__ == "__main__":
    main()
