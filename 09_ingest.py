"""
统一接入入口 —— 一个命令接入任意格式的数据集
================================================

按格式分发到对应适配器（sources.py），把元数据写进目录。
这就是文档的"新增数据源(Onboarding)"工作流的入口。

用法：
    python 09_ingest.py <格式> <标识或路径> [更多...]

格式（<格式> 可选值）：
    lerobot_hf   HuggingFace 上的 LeRobot 数据集，标识=repo_id
                 例: python 09_ingest.py lerobot_hf lerobot/pusht lerobot/aloha_sim_insertion_human
    openx_rlds   Open X-Embodiment / RLDS，标识=数据集名 或 name@version 或 dataset_info.json URL
                 例: python 09_ingest.py openx_rlds fractal20220817_data
    hdf5         本地 .hdf5/.h5 文件，标识=文件路径
                 例: python 09_ingest.py hdf5 ./my_data.hdf5
    mcap         本地 .mcap 文件，标识=文件路径
                 例: python 09_ingest.py mcap ./recording.mcap

不带参数则打印帮助。
"""

import sys
import duckdb
import sources
import hub_data as hd
from schema import CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE, insert_sql, to_db_values

INSERT_DATASET = insert_sql("datasets", hd.DatasetMeta)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("已注册的格式适配器：", sources.available())
        return

    source_type = sys.argv[1]
    identifiers = sys.argv[2:]

    con = hd.ensure_catalog()        # 自动建表/迁移；若被占用会报锁，请先关网页
    con.execute(CREATE_DATASETS_TABLE)
    con.execute(CREATE_EPISODES_TABLE)

    ok = 0
    for ident in identifiers:
        try:
            meta = sources.fetch(source_type, ident)
            con.execute("DELETE FROM datasets WHERE dataset_id = ?", [meta.dataset_id])
            con.execute(INSERT_DATASET, to_db_values(meta))
            ok += 1
            print(f"[ok] {source_type:<11} {ident}  ->  {meta.dataset_id} "
                  f"({meta.embodiment}, {meta.n_episodes} eps, {meta.source_format})")
        except Exception as e:
            print(f"[skip] {source_type:<11} {ident}: {repr(e)[:160]}")

    print(f"\n成功接入 {ok}/{len(identifiers)} 个。当前目录：")
    print(con.execute(
        "SELECT name, source_format, embodiment, license_spdx, n_episodes "
        "FROM datasets ORDER BY name"
    ).df().to_string(index=False))

    # 自动给新接入的数据集补算语义向量（增量；没装 sentence-transformers 会安全跳过）
    try:
        import embeddings
        embeddings.embed_missing(con, quiet=False)
    except Exception as e:
        print(f"[embeddings] 跳过：{repr(e)[:80]}")

    con.close()


if __name__ == "__main__":
    main()
