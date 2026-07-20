"""
步骤 10：给数据集算语义向量（增量，供跨语言语义搜索用）
=======================================================

默认**只给还没算过的数据集**补向量（增量，规模大也不怕）；
加 --all 才全量重算。接入新数据后通常不用手动跑——09/11 会自动补算。

需要 pip install sentence-transformers（首次下载多语言小模型）。
先关后端避免数据库锁：
    python 13_build_embeddings.py          # 增量：只补缺的
    python 13_build_embeddings.py --all    # 全量重算
"""

import sys
import hub_data as hd
import embeddings


def main():
    force = "--all" in sys.argv
    try:
        con = hd.ensure_catalog()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑 uvicorn 的终端按 Ctrl+C 关闭后端再运行。")
            return
        raise

    n = embeddings.embed_missing(con, force=force)
    total = con.execute("SELECT COUNT(*) FROM dataset_embeddings").fetchone()[0]
    print(f"完成：本次新算 {n} 条；目录共有 {total} 条向量。")
    if n > 0:
        print("重启后端 uvicorn 后，搜索框即支持跨语言语义搜索（搜'杯子'命中 cup）。")
    con.close()


if __name__ == "__main__":
    main()
