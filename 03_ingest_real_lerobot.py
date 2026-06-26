"""
步骤 2.5：接入【真实】LeRobot 数据集的元数据 → DuckDB
=======================================================

只下载几 KB 的元数据文件（meta/info.json），不下载几十 GB 的视频/parquet，
就能把真实数据集登记进目录。这演示了"联邦接入：元数据先行，原始数据按需取"。

用法（需联网，能访问 huggingface.co）：
    python 03_ingest_real_lerobot.py lerobot/pusht lerobot/aloha_sim_insertion_human

不带参数则用一组默认的小数据集。结果追加进 catalog.duckdb，可再用 02 里的 SQL 检索。
"""

import sys
import json
import duckdb
from schema import (
    DatasetMeta, infer_commercial_use,
    CREATE_DATASETS_TABLE, CREATE_EPISODES_TABLE,
)

DB_PATH = "catalog.duckdb"
DEFAULT_REPOS = ["lerobot/pusht", "lerobot/aloha_sim_insertion_human"]


def guess_embodiment(robot_type: str) -> str:
    """从 robot_type 粗略推断本体类别。"""
    r = (robot_type or "").lower()
    if "aloha" in r or "bimanual" in r or "dual" in r:
        return "bimanual"
    if "humanoid" in r or "h1" in r or "g1" in r or "agibot" in r:
        return "humanoid"
    if "mobile" in r:
        return "mobile"
    return "single_arm"


def fetch_dataset_meta(repo_id: str) -> DatasetMeta:
    """只拉 meta/info.json + 数据集卡片里的 license，组装成 DatasetMeta。"""
    from huggingface_hub import hf_hub_download, dataset_info

    info_path = hf_hub_download(repo_id, "meta/info.json", repo_type="dataset")
    info = json.load(open(info_path))

    # license 不在 info.json 里，从数据集卡片元数据取
    license_str = "unknown"
    try:
        di = dataset_info(repo_id)
        license_str = (di.card_data or {}).get("license", "unknown") or "unknown"
    except Exception:
        pass

    features = info.get("features", {})
    cam_keys = [k for k, v in features.items() if v.get("dtype") in ("video", "image")]
    robot_type = info.get("robot_type", "")

    return DatasetMeta(
        dataset_id=repo_id,
        name=repo_id.split("/")[-1],
        source="huggingface",
        source_format=f"lerobot_{info.get('codebase_version', 'v?')}",
        license=license_str,
        commercial_use=infer_commercial_use(license_str),
        n_episodes=int(info.get("total_episodes", 0)),
        total_frames=int(info.get("total_frames", 0)),
        fps=float(info.get("fps", 0) or 0),
        embodiment=guess_embodiment(robot_type),
        robot_model=robot_type,
        n_cameras=len(cam_keys),
        has_failure_labels="next.reward" in features or "success" in features,
        collection="",
        homepage=f"https://huggingface.co/datasets/{repo_id}",
    )


def main():
    repos = sys.argv[1:] or DEFAULT_REPOS
    con = duckdb.connect(DB_PATH)
    con.execute(CREATE_DATASETS_TABLE)
    con.execute(CREATE_EPISODES_TABLE)

    for repo in repos:
        try:
            meta = fetch_dataset_meta(repo)
            con.execute("DELETE FROM datasets WHERE dataset_id = ?", [repo])
            con.execute(
                "INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                tuple(meta.to_row().values()),
            )
            print(f"[ok] {repo}: {meta.n_episodes} eps, {meta.embodiment}, "
                  f"fps={meta.fps}, license={meta.license}, cams={meta.n_cameras}")
        except Exception as e:
            print(f"[skip] {repo}: {repr(e)[:140]}")

    print("\n当前目录里的数据集：")
    print(con.execute(
        "SELECT name, source_format, embodiment, license, commercial_use, n_episodes "
        "FROM datasets ORDER BY n_episodes DESC"
    ).df().to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
