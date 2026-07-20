"""
刷新流水线（自动化摄入）——让目录保持新鲜
============================================

一次刷新做三件事（对应文档"新增数据源 Onboarding"工作流）：
  1) 增量接入新数据集（11_batch_ingest 内部会自动补语义向量 + 概念标签）
  2) 链接健康检查（把失效指针写回 link_health 表，对应文档风险"联邦指针失效"）

设计成幂等、可重复：已接入的覆盖更新、新数据集追加、向量增量补。
既可手动跑一次，也可由 scheduler.py 定时跑。

用法：
    python pipeline.py                 # 用环境变量的默认配置跑一次
    python pipeline.py --limit 50 --task robotics
配置（环境变量，供 Docker 调度用）：
    MDH_INGEST_LIMIT   每轮接入目标数（默认 50）
    MDH_INGEST_TASK    任务类别枚举，如 robotics（优先级高于 authors）
    MDH_INGEST_AUTHORS 多家来源账号(逗号)，如 lerobot,agibot-world
"""

import os
import sys
import time
import argparse
import subprocess


def _run(script_args):
    """用当前 Python 跑一个脚本，实时打印输出。"""
    print(f"\n$ python {' '.join(script_args)}")
    subprocess.run([sys.executable, *script_args], check=False)


def run(limit=None, authors=None, task=None):
    limit = str(limit or os.environ.get("MDH_INGEST_LIMIT", "50"))
    task = task if task is not None else os.environ.get("MDH_INGEST_TASK", "")
    authors = authors if authors is not None else os.environ.get("MDH_INGEST_AUTHORS", "")

    print(f"\n========== 刷新开始 {time.strftime('%Y-%m-%d %H:%M:%S')} ==========")

    # 1) 增量接入（11 内部：抓元数据 → 自动补向量 → 刷概念标签）
    ingest = ["11_batch_ingest.py", "--limit", limit]
    if task:
        ingest += ["--task", task]
    elif authors:
        ingest += ["--authors", authors]
    _run(ingest)

    # 2) 链接健康检查（写回 link_health 表）
    _run(["07_check_links.py", "--write"])

    print(f"========== 刷新完成 {time.strftime('%Y-%m-%d %H:%M:%S')} ==========\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--authors", default=None)
    args = ap.parse_args()
    run(limit=args.limit, authors=args.authors, task=args.task)
