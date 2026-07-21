"""
步骤 5：联邦指针健康检查（对应文档第 8 章风险"联邦指针失效"）
================================================================

联邦目录只存"指向源的链接"，源随时可能被删/改名 → 链接失效。
本脚本扫一遍目录里所有数据集的主页链接，逐个发请求看是否还活着，
把失效的（404 / 打不开）标出来。

用 requests 库（自带正确的 SSL 证书，避免 macOS 上 Python 证书为空的坑）。需要联网。

用法：
    python 07_check_links.py
"""

import os
import hub_data as hd

UA = {"User-Agent": "mini-datahub-linkcheck/1.0"}

# 若配了 HF 镜像（如国内服务器 HF_ENDPOINT=https://hf-mirror.com），
# 体检 HF 链接时改走镜像域名，避免"连不上 huggingface.co"造成的误报。
_HF_MIRROR = os.environ.get("HF_ENDPOINT", "").strip().rstrip("/")


def _apply_mirror(url: str) -> str:
    if _HF_MIRROR and url and "huggingface.co" in url:
        host = _HF_MIRROR.split("://", 1)[-1]      # hf-mirror.com
        return url.replace("huggingface.co", host)
    return url


def check_url(url, timeout=8):
    """返回 (alive: bool, status: 状态码或错误简述)。"""
    if not url:
        return False, "无链接"
    url = _apply_mirror(url)
    try:
        import requests
    except ImportError:
        return False, "需要 requests：pip install requests"
    try:
        # 先 HEAD（快）；部分服务器不支持 HEAD，再退回 GET
        r = requests.head(url, allow_redirects=True, timeout=timeout, headers=UA)
        if r.status_code in (400, 403, 405, 501):
            r = requests.get(url, allow_redirects=True, timeout=timeout,
                             headers=UA, stream=True)
        return (r.status_code < 400), r.status_code
    except requests.exceptions.SSLError:
        return False, "SSL证书错误(装 certifi 或运行 Install Certificates)"
    except requests.exceptions.RequestException as e:
        return False, type(e).__name__


def main():
    import argparse
    import time
    import store
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="把检查结果写回 link_health 表")
    ap.add_argument("--workers", type=int, default=16, help="并发检查线程数")
    args = ap.parse_args()

    # --write 需要写库 -> DuckDB 用读写连接；只读检查时才用只读
    ro = (not store.is_pg()) and (not args.write)
    try:
        con = store.connect(read_only=ro)
        rows = store.run(con, "SELECT dataset_id, name, homepage FROM datasets ORDER BY name")
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：DuckDB 请先关后端；或用 Postgres（可并发）。")
            return
        print("[提示] 还没有目录，请先接入数据。")
        return

    print(f"并发检查 {len(rows)} 个数据集的主页链接…")
    from concurrent.futures import ThreadPoolExecutor
    def check(row):
        did, name, homepage = row
        alive, status = check_url(homepage)
        return (did, name, homepage, alive, str(status))
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(check, rows))

    dead = sum(1 for r in results if not r[3])
    for did, name, homepage, alive, status in results:
        if not alive:
            print(f"❌ {status:<28} {name:<28} {homepage}")

    print(f"\n小结：{len(rows)} 个里 {dead} 个链接失效。")

    if args.write:
        # 写回 link_health 表：门户可据此标记失效数据集（对应文档"联邦指针失效"风险）
        store.run(con, "CREATE TABLE IF NOT EXISTS link_health "
                       "(dataset_id VARCHAR PRIMARY KEY, alive BOOLEAN, status VARCHAR, checked_at VARCHAR)")
        store.run(con, "DELETE FROM link_health")
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        store.run_many(con, "INSERT INTO link_health VALUES (?, ?, ?, ?)",
                       [(did, alive, status, ts) for did, name, homepage, alive, status in results])
        print(f"[link_health] 已写回 {len(results)} 条检查结果（{dead} 个失效）。")


if __name__ == "__main__":
    main()
