"""
基础账户功能（demo）—— 注册 / 登录 + 持久化收藏集
====================================================

对齐"账户功能 MVP"：先做最贴核心价值的一块——把临时购物车升级成【存到账户下的
命名收藏集】，让研究者的数据选型能沉淀、复用、复现。

设计：
  - 走 store 抽象，DuckDB / Postgres 通用（线上是 Postgres，读写无锁问题）。
  - 密码用标准库 pbkdf2_hmac 加盐哈希，不存明文；会话用随机 token（存 sessions 表）。
  - demo 级安全：够研究预览用；上生产还需 HTTPS、限流、token 过期等加固。
"""

import time
import uuid
import hashlib
import secrets

import store


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ensure_tables(con):
    store.run(con, "CREATE TABLE IF NOT EXISTS users "
              "(username VARCHAR PRIMARY KEY, pw_hash VARCHAR, salt VARCHAR, created_at VARCHAR)")
    store.run(con, "CREATE TABLE IF NOT EXISTS sessions "
              "(token VARCHAR PRIMARY KEY, username VARCHAR, created_at VARCHAR)")
    store.run(con, "CREATE TABLE IF NOT EXISTS collections "
              "(id VARCHAR PRIMARY KEY, username VARCHAR, name VARCHAR, created_at VARCHAR)")
    store.run(con, "CREATE TABLE IF NOT EXISTS collection_items "
              "(collection_id VARCHAR, dataset_id VARCHAR)")


def _hash(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000).hex()


# ---------------- 认证 ----------------
def register(con, username: str, password: str):
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return None, "用户名和密码不能为空"
    if len(username) > 40:
        return None, "用户名过长"
    if len(password) < 6:
        return None, "密码至少 6 位"
    if store.one(con, "SELECT 1 FROM users WHERE username = ?", [username]):
        return None, "用户名已存在"
    salt = secrets.token_hex(16)
    store.run(con, "INSERT INTO users VALUES (?, ?, ?, ?)",
              [username, _hash(password, salt), salt, _now()])
    return username, None


def login(con, username: str, password: str):
    row = store.one(con, "SELECT pw_hash, salt FROM users WHERE username = ?", [username])
    if not row or _hash(password or "", row[1]) != row[0]:
        return None, "用户名或密码错误"
    token = secrets.token_urlsafe(32)
    store.run(con, "INSERT INTO sessions VALUES (?, ?, ?)", [token, username, _now()])
    return token, None


def user_for_token(con, token: str):
    if not token:
        return None
    row = store.one(con, "SELECT username FROM sessions WHERE token = ?", [token])
    return row[0] if row else None


def logout(con, token: str):
    if token:
        store.run(con, "DELETE FROM sessions WHERE token = ?", [token])


# ---------------- 收藏集 ----------------
def create_collection(con, username: str, name: str, ids):
    cid = uuid.uuid4().hex
    store.run(con, "INSERT INTO collections VALUES (?, ?, ?, ?)",
              [cid, username, (name or "未命名收藏集").strip()[:60], _now()])
    ids = [i for i in (ids or []) if i]
    if ids:
        store.run_many(con, "INSERT INTO collection_items VALUES (?, ?)",
                       [(cid, i) for i in ids])
    return cid


def list_collections(con, username: str):
    rows = store.run(con,
        "SELECT c.id, c.name, c.created_at, COUNT(ci.dataset_id) "
        "FROM collections c LEFT JOIN collection_items ci ON c.id = ci.collection_id "
        "WHERE c.username = ? GROUP BY c.id, c.name, c.created_at ORDER BY c.created_at DESC",
        [username])
    return [{"id": r[0], "name": r[1], "created_at": r[2], "count": int(r[3] or 0)} for r in rows]


def collection_ids(con, cid: str, username: str):
    owner = store.one(con, "SELECT username FROM collections WHERE id = ?", [cid])
    if not owner or owner[0] != username:
        return None
    return [r[0] for r in store.run(con,
            "SELECT dataset_id FROM collection_items WHERE collection_id = ?", [cid])]


def delete_collection(con, cid: str, username: str) -> bool:
    owner = store.one(con, "SELECT username FROM collections WHERE id = ?", [cid])
    if not owner or owner[0] != username:
        return False
    store.run(con, "DELETE FROM collection_items WHERE collection_id = ?", [cid])
    store.run(con, "DELETE FROM collections WHERE id = ?", [cid])
    return True
