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
    """返回 (verdict, status, final_url)。

    verdict 三态 —— 区分"真失效"与"我们连不上"，避免误报：
      "alive"   链接正常（含被重定向到新地址）
      "dead"    源端明确说没了（404/410）—— 这才是真的失效
      "unknown" 我们这边连不上（网络受限/超时/SSL），**不能**判定为失效

    final_url：若发生永久重定向，返回新地址，供自动修复写回数据库。
    """
    if not url:
        return "dead", "无链接", None
    probe = _apply_mirror(url)
    try:
        import requests
    except ImportError:
        return "unknown", "需要 requests", None
    try:
        r = requests.head(probe, allow_redirects=True, timeout=timeout, headers=UA)
        if r.status_code in (400, 403, 405, 501):
            r = requests.get(probe, allow_redirects=True, timeout=timeout,
                             headers=UA, stream=True)
        code = r.status_code
        if code in (404, 410):
            return "dead", code, None
        if code < 400:
            # 跟随重定向后的最终地址（用于自动修复改名/迁移的数据集）
            final = r.url if (r.url and r.url.rstrip("/") != probe.rstrip("/")) else None
            return "alive", code, final
        # 401/403(需登录/gated)、5xx(源端故障) —— 都不算"数据集没了"
        return "unknown", code, None
    except requests.exceptions.SSLError:
        return "unknown", "SSLError", None
    except requests.exceptions.RequestException as e:
        # ConnectionError / Timeout：多为**我们这边**网络不可达，不判失效
        return "unknown", type(e).__name__, None


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
        verdict, status, final = check_url(homepage)
        return (did, name, homepage, verdict, str(status), final)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(check, rows))

    # 读取历史连续失败次数（连续 N 次才判定失效，消除偶发抖动）
    prev = {}
    try:
        for r in store.run(con, "SELECT dataset_id, fail_count FROM link_health"):
            prev[r[0]] = int(r[1] or 0)
    except Exception:
        pass

    FAIL_THRESHOLD = 3
    n_alive = n_dead = n_unknown = n_fixed = 0
    records, fixes = [], []
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    for did, name, homepage, verdict, status, final in results:
        if verdict == "alive":
            fails = 0
            n_alive += 1
            if final:                      # 自动修复：跟随重定向，写回新地址
                fixes.append((final, did))
                n_fixed += 1
                print(f"🔁 自动修复 {name[:30]:<32} -> {final[:60]}")
        elif verdict == "dead":
            fails = prev.get(did, 0) + 1
            n_dead += 1
            print(f"❌ {status:<14} {name[:28]:<30} {homepage}")
        else:                              # unknown：我们连不上，不算失效
            fails = prev.get(did, 0)       # 不累加，避免网络问题把好数据集拖黑
            n_unknown += 1

        # 只有"确认失效"且连续达阈值，才在前端标红
        alive_flag = not (verdict == "dead" and fails >= FAIL_THRESHOLD)
        records.append((did, alive_flag, verdict, status, fails, ts))

    print(f"\n小结：共 {len(rows)} 个 —— 正常 {n_alive}，确认失效 {n_dead}，"
          f"无法验证(我方网络受限) {n_unknown}，自动修复 {n_fixed}")
    if n_unknown:
        print("提示：'无法验证'多为本机网络访问不到源站（如国内访问 github.io/GCS），"
              "不代表数据集失效，前端不会标红。")

    if args.write:
        if fixes:                          # 把重定向后的新地址写回，真正"自动修复"
            store.run_many(con, "UPDATE datasets SET homepage = ? WHERE dataset_id = ?", fixes)
            print(f"[修复] 已更新 {len(fixes)} 个数据集的主页地址。")

        store.run(con, "CREATE TABLE IF NOT EXISTS link_health "
                       "(dataset_id VARCHAR PRIMARY KEY, alive BOOLEAN, verdict VARCHAR, "
                       "status VARCHAR, fail_count BIGINT, checked_at VARCHAR)")
        # 兼容旧表结构：缺列则补
        try:
            cols = set(store.table_columns(con, "link_health"))
            for c, t in (("verdict", "VARCHAR"), ("fail_count", "BIGINT")):
                if c not in cols:
                    store.run(con, store.ddl(f"ALTER TABLE link_health ADD COLUMN {c} {t}"))
        except Exception:
            pass
        store.run(con, "DELETE FROM link_health")
        store.run_many(con, "INSERT INTO link_health VALUES (?, ?, ?, ?, ?, ?)", records)
        flagged = sum(1 for r in records if not r[1])
        print(f"[link_health] 已写回 {len(records)} 条（前端标红 {flagged} 个）。")


if __name__ == "__main__":
    main()
