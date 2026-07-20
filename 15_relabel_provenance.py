"""
一次性重标 provenance（采集方式）—— 修正历史上写死的 "teleop"
================================================================

老数据把所有 provenance_type 写死成 teleop（不严谨）。本脚本按与 sources.py
相同的启发式重判：有仿真信号 -> simulation，否则 -> unknown（不假装 teleop）。

用法（DuckDB 需先停后端；Postgres 可并发）：
    python 15_relabel_provenance.py           # 应用
    python 15_relabel_provenance.py --dry     # 只看会怎么改，不写库
"""

import argparse
import store
from sources import _detect_provenance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只预览不写库")
    args = ap.parse_args()

    con = store.connect(read_only=args.dry and not store.is_pg())
    rows = store.run(con, "SELECT dataset_id, name, robot_model, provenance_type FROM datasets")

    changes = []
    for did, name, robot, old in rows:
        new = _detect_provenance(did, name, robot)
        if new != old:
            changes.append((did, old, new))

    for did, old, new in changes:
        print(f"  {did:<45} {old} -> {new}")
    print(f"\n将变更 {len(changes)}/{len(rows)} 条。")

    if args.dry:
        print("(dry run，未写库)")
        return
    for did, _, new in changes:
        store.run(con, "UPDATE datasets SET provenance_type = ? WHERE dataset_id = ?", [new, did])
    print("[ok] 已写回。")


if __name__ == "__main__":
    main()
