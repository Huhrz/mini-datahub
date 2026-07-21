"""
数据库抽象层 —— 同一套代码可跑 DuckDB（本地零配置）或 Postgres（生产可并发）
================================================================================

为什么要它：DuckDB 是单写锁——后端只读时摄入没法写，必须先停后端。
Postgres 是客户端-服务器数据库，**后端和摄入可以同时读写**，这是"能上线产品"的必要条件。

如何选择后端：环境变量 MDH_DB
  - 不设 或 文件名（如 catalog.duckdb） -> DuckDB（默认，本地开发）
  - postgresql://user:pass@host:5432/db  -> Postgres（生产）

上层代码统一用本模块的 run / run_df / run_many 等，SQL 里一律用 ? 占位符，
本模块自动为 Postgres 翻译成 %s，并处理类型/自省差异。
"""

import os

DB_URL = os.environ.get("MDH_DB", "catalog.duckdb")


def is_pg() -> bool:
    return DB_URL.split(":", 1)[0] in ("postgres", "postgresql")


def connect(read_only: bool = False):
    if is_pg():
        import psycopg
        return psycopg.connect(DB_URL, autocommit=True)
    import duckdb
    return duckdb.connect(DB_URL, read_only=read_only)


def _pg(sql: str) -> str:
    """把 ? 占位符换成 Postgres 的 %s（简单场景够用）。"""
    return sql.replace("?", "%s")


def ddl(sql: str) -> str:
    """DuckDB DDL -> Postgres：DOUBLE 需写成 DOUBLE PRECISION。
    用单次 replace —— Python 的 str.replace 从左到右不回扫替换文本，
    所以每个 DOUBLE 只会变成一个 DOUBLE PRECISION，不会出现 PRECISION PRECISION。"""
    if is_pg():
        return sql.replace("DOUBLE", "DOUBLE PRECISION")
    return sql


def run(con, sql: str, params=None):
    """执行并返回行列表（DDL/INSERT 返回 []）。"""
    params = params or []
    if is_pg():
        with con.cursor() as cur:
            cur.execute(_pg(sql), params)
            try:
                return cur.fetchall()
            except Exception:
                return []
    r = con.execute(sql, params)
    try:
        return r.fetchall()
    except Exception:
        return []


def one(con, sql: str, params=None):
    rows = run(con, sql, params)
    return rows[0] if rows else None


def run_many(con, sql: str, rows):
    if is_pg():
        with con.cursor() as cur:
            cur.executemany(_pg(sql), list(rows))
    else:
        con.executemany(sql, list(rows))


def run_df(con, sql: str, params=None):
    """返回 pandas DataFrame。"""
    import pandas as pd
    params = params or []
    if is_pg():
        with con.cursor() as cur:
            cur.execute(_pg(sql), params)
            cols = [d.name for d in cur.description] if cur.description else []
            return pd.DataFrame(cur.fetchall(), columns=cols)
    return con.execute(sql, params).df()


def has_column(con, table: str, col: str) -> bool:
    if is_pg():
        rows = run(con,
                   "SELECT 1 FROM information_schema.columns WHERE table_name=? AND column_name=?",
                   [table, col])
        return len(rows) > 0
    try:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return col in cols
    except Exception:
        return False


def table_columns(con, table: str):
    if is_pg():
        return [r[0] for r in run(con,
                "SELECT column_name FROM information_schema.columns WHERE table_name=?", [table])]
    try:
        return [r[1] for r in con.execute(f"PRAGMA table_info('{table}')").fetchall()]
    except Exception:
        return []


def close(con):
    try:
        con.close()
    except Exception:
        pass
