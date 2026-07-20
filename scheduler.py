"""
定时调度器——每隔 N 小时自动跑一次刷新流水线
================================================

这是"产品 vs Demo"的分水岭：数据 hub 的生命线是"数据不过期"。
调度器让接入新数据、补向量、健康检查全自动化，无需人工。

轻量实现（不引额外依赖）：启动即先跑一次，然后每隔 MDH_SCHEDULE_HOURS 小时再跑。
生产里由 docker-compose 的 scheduler 服务常驻运行。

    python scheduler.py           # 前台常驻
配置：
    MDH_SCHEDULE_HOURS   刷新间隔小时数（默认 24）
    （其余接入配置见 pipeline.py：MDH_INGEST_LIMIT/TASK/AUTHORS）

注意：调度器会【写库】，因此生产请用 Postgres（MDH_DB=postgresql://...），
这样它和后端可同时读写；DuckDB 下会和后端抢写锁。
"""

import os
import time
import traceback

import pipeline


def main():
    hours = float(os.environ.get("MDH_SCHEDULE_HOURS", "24"))
    print(f"[scheduler] 已启动：每 {hours} 小时刷新一次；先立即跑一轮。")
    while True:
        try:
            pipeline.run()
        except Exception:
            print("[scheduler] 本轮刷新出错：")
            traceback.print_exc()
        print(f"[scheduler] 休眠 {hours} 小时至下一轮…")
        time.sleep(hours * 3600)


if __name__ == "__main__":
    main()
