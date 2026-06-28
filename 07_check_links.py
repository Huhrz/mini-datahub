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

import hub_data as hd

UA = {"User-Agent": "mini-datahub-linkcheck/1.0"}


def check_url(url, timeout=8):
    """返回 (alive: bool, status: 状态码或错误简述)。"""
    if not url:
        return False, "无链接"
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
    try:
        con = hd.get_connection(hd.DB_PATH, read_only=True)
        rows = con.execute(
            "SELECT dataset_id, name, homepage FROM datasets ORDER BY name"
        ).fetchall()
    except Exception as e:
        if "lock" in str(e).lower():
            print("[提示] 数据库被占用：请先在跑 streamlit 的终端按 Ctrl+C 关闭网页再试。")
            return
        print("[提示] 还没有目录，请先运行 02 或 03 生成 catalog.duckdb。")
        return

    print(f"检查 {len(rows)} 个数据集的主页链接…\n")
    print(f"{'状态':<6}{'数据集':<24}{'链接'}")
    dead = 0
    for did, name, homepage in rows:
        alive, status = check_url(homepage)
        mark = "✅ ok" if alive else f"❌ {status}"
        if not alive:
            dead += 1
        print(f"{mark:<6} {name:<22} {homepage}")

    print(f"\n小结：{len(rows)} 个里 {dead} 个链接失效。")
    if dead:
        print("失效的链接说明源已被删/改名，真实系统里应触发告警或降级转存（文档第 8 章风险）。")


if __name__ == "__main__":
    main()
