"""
自建可视化的后端提取器（替代 HuggingFace 的 iframe 页面）
============================================================

目标：给定 dataset_id + episode，产出一份"播放器能直接吃"的数据：
    {cameras:[{name,url}], series:{name:[...]}, fps, n_frames, ...}

联邦原则不变：**视频给客户端直连源 CDN 的 URL（fetch-through 流式播放），
我们不把视频落盘再托管**。播放器的 UI/时间轴/曲线都是我们自己的，
只有媒体字节从源头 CDN 流过来——这和"把别人整个网站塞进 iframe"根本不同。

目前覆盖 LeRobot/HF 格式（我们的规范格式，覆盖 HF 及任何 lerobot 布局的源）。
其它格式（HDF5 / RLDS / MCAP）按同样的返回结构逐步补适配器即可。

路径模板不写死：从每个数据集自己的 meta/info.json 读取 data_path / video_path
模板再套入 episode 号，所以对 v2.0 / v2.1 这类"每 episode 一个 mp4"的布局通用。
v3.0 把多个 episode 打包进一个文件、无法按 URL 切片单集视频——这种情况优雅降级：
只给状态/动作曲线并给出说明。
"""

import json
import functools

HF = "https://huggingface.co/datasets"


@functools.lru_cache(maxsize=256)
def _info(repo_id: str) -> dict:
    """读并缓存 meta/info.json（同一数据集只拉一次）。"""
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id, "meta/info.json", repo_type="dataset")
    return json.load(open(p))


def _video_keys(info: dict):
    feats = info.get("features", {})
    return [k for k, v in feats.items() if v.get("dtype") == "video"]


def _cam_name(key: str) -> str:
    # observation.images.top -> top
    return key.split(".")[-1]


def _fmt(template: str, **kw):
    """套模板；缺键就抛 KeyError，交给调用方兜底。"""
    return template.format(**kw)


def _episode_urls(repo_id: str, info: dict, ep: int):
    """按 info.json 的模板拼出该 episode 每路相机的 mp4 直链。
    仅适用于模板里带 {episode_index} 的按集布局（v2.x）。"""
    tmpl = info.get("video_path")
    if not tmpl or "episode_index" not in tmpl:
        return []          # v3 打包布局或无模板 -> 不可按 URL 切片
    chunks = int(info.get("chunks_size", 1000) or 1000)
    chunk = ep // chunks
    base = f"{HF}/{repo_id}/resolve/main/"
    cams = []
    for vk in _video_keys(info):
        try:
            rel = _fmt(tmpl, episode_chunk=chunk, video_key=vk, episode_index=ep)
            cams.append({"name": _cam_name(vk), "url": base + rel})
        except Exception:
            continue
    return cams


def _url_alive(url: str, timeout=8) -> bool:
    try:
        import requests
        r = requests.head(url, allow_redirects=True, timeout=timeout,
                          headers={"User-Agent": "mini-datahub/1.0"})
        if r.status_code in (403, 405, 501):     # 有些 CDN 不认 HEAD
            r = requests.get(url, allow_redirects=True, timeout=timeout, stream=True,
                            headers={"User-Agent": "mini-datahub/1.0"})
        return r.status_code < 400
    except Exception:
        return False


# ---------------- 对外：缩略图（极轻，只读 info.json，不碰 meta/episodes、不用 httpfs）----------------
def _first_video_url(repo_id: str, info: dict):
    """第一路相机、打包/首集视频的直链 —— 打包 mp4 的首个文件首帧 = 第 0 集起始帧，
    所以缩略图只需按 info.json 的模板拼 URL，v2.x / v3.0 都不用读元数据。"""
    vks = _video_keys(info)
    tmpl = info.get("video_path")
    if not vks or not tmpl:
        return None
    vk = vks[0]
    base = f"{HF}/{repo_id}/resolve/main/"
    for kw in ({"video_key": vk, "chunk_index": 0, "file_index": 0},        # v3.0 打包
               {"video_key": vk, "episode_chunk": 0, "episode_index": 0}):  # v2.x 按集
        try:
            return base + tmpl.format(**kw)
        except Exception:
            continue
    return None


@functools.lru_cache(maxsize=512)
def preview(repo_id: str) -> dict:
    """卡片缩略图：第一路相机首个视频文件（浏览器 <video> 首帧即缩略图）。
    只读 info.json（几 KB）+ 一次 HEAD，绝不碰 meta/episodes / httpfs / 大文件。"""
    try:
        info = _info(repo_id)
    except Exception:
        return {}
    url = _first_video_url(repo_id, info)
    if not url:
        return {}
    # 不做 HEAD 存活检查（20 张卡并发 HEAD 易超时导致漏图）；URL 按模板拼好，
    # 前端 <video> 加载失败会自动回退占位图标。
    return {"video": url, "name": _cam_name(_video_keys(info)[0]), "fps": float(info.get("fps") or 0)}


# ---------------- 对外：完整一集（相机 + 曲线） ----------------
def _extract_series(df, max_dims=12, max_points=300) -> dict:
    """把 action / observation.state 的多维列，降采样成可画的折线序列。"""
    out = {}
    n = len(df)
    if n == 0:
        return out
    step = max(1, n // max_points)
    idx = list(range(0, n, step))
    for col, short in (("action", "action"), ("observation.state", "state")):
        if col not in df.columns:
            continue
        vals = df[col].tolist()
        if not vals:
            continue
        try:
            width = len(vals[0])
        except TypeError:
            # 标量列
            out[short] = [float(vals[i]) for i in idx]
            continue
        width = min(width, max_dims)
        for d in range(width):
            try:
                out[f"{short}[{d}]"] = [float(vals[i][d]) for i in idx]
            except Exception:
                pass
    return out


# ================= LeRobot v3.0（打包布局）支持 =================
# v3.0 把多条轨迹打包进同一个 mp4/parquet。要放"第 ep 集"，需要读 meta/episodes
# 里该集的记录，拿到它在打包 mp4 里的 from_timestamp~to_timestamp（时间片），
# 以及它的数据 parquet 文件位置。播放时不转码：把整段打包 mp4 直链给 <video>，
# 播放器自己把播放约束在 [from,to] 区间里循环（见 EpisodePlayer.jsx）。

def _is_packed(info: dict) -> bool:
    """v3.0：video/data 模板里没有 {episode_index}，是按文件打包而非按集一个文件。"""
    vp = info.get("video_path") or ""
    dp = info.get("data_path") or ""
    return ("episode_index" not in vp) or ("episode_index" not in dp)


def _get(rec: dict, *names, default=None):
    """从一行记录里按多个候选列名取值（容忍 v3 schema 细节差异）。"""
    for n in names:
        if n in rec and rec[n] is not None:
            return rec[n]
    return default


def _fuzzy(rec: dict, *must, default=None):
    """模糊取值：返回第一个"键名同时包含所有 must 子串"的列值（兜底 schema 命名差异）。"""
    for k, v in rec.items():
        kl = str(k).lower()
        if v is not None and all(m.lower() in kl for m in must):
            return v
    return default


@functools.lru_cache(maxsize=64)
def _v3_episode_files(repo_id: str):
    """列出 meta/episodes 下的分片文件（排序），只列名不下载。"""
    from huggingface_hub import list_repo_files
    files = sorted(f for f in list_repo_files(repo_id, repo_type="dataset")
                   if f.startswith("meta/episodes/") and f.endswith(".parquet"))
    return tuple(files)


_LOC_HINTS = ("chunk", "file", "timestamp", "from", "to", "length", "episode", "index")


def _loc_cols(cols):
    """只保留"定位用"的标量列（chunk/file/时间戳/episode_index），
    跳过 episodes 表里可能高达几十 MB 的大数组列 —— 只拉这些列，range 请求几十 KB。"""
    keep = [c for c in cols if c == "episode_index" or any(h in c.lower() for h in _LOC_HINTS)]
    return keep or cols


def _read_locators_remote(con, url):
    cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{url}')").fetchall()]
    sel = ", ".join(f'"{c}"' for c in _loc_cols(cols))
    return con.execute(f"SELECT {sel} FROM read_parquet('{url}')").df()


def _pick_record(df0, ep, con, base, files):
    """从定位列表里取第 ep 集；不在首片就估算目标片再读 1 个；都不中给首行。"""
    if df0 is None or df0.empty:
        return None
    if "episode_index" not in df0.columns:
        return df0.iloc[0].to_dict()
    hit = df0[df0["episode_index"] == ep]
    if not hit.empty:
        return hit.iloc[0].to_dict()
    try:
        mn, mx = int(df0["episode_index"].min()), int(df0["episode_index"].max())
        per = mx - mn + 1
        if per > 0 and len(files) > 1:
            idx = min((ep - mn) // per, len(files) - 1)
            if idx != 0:
                dfx = _read_locators_remote(con, base + files[idx])
                if dfx is not None and "episode_index" in dfx.columns:
                    hit = dfx[dfx["episode_index"] == ep]
                    if not hit.empty:
                        return hit.iloc[0].to_dict()
    except Exception:
        pass
    return df0.iloc[0].to_dict()


def _v3_record(repo_id: str, ep: int):
    """取第 ep 集的记录 —— **严格有界，最多碰 2 个分片，且只拉定位列（range 请求）**。
    meta/episodes 可能有上百个分片、单文件甚至几十 MB，逐个整份下载会失控
    （就是"一直在下"的元凶）。优先用 duckdb httpfs 远程按列读；失败再退回有界本地下载。"""
    files = _v3_episode_files(repo_id)
    if not files:
        return None
    base = f"{HF}/{repo_id}/resolve/main/"

    # 首选：远程 httpfs 只读定位列（避开几十 MB 的大文件整份下载）
    try:
        import duckdb
        con = duckdb.connect()
        try:
            con.execute("INSTALL httpfs; LOAD httpfs;")
            df0 = _read_locators_remote(con, base + files[0])
            rec = _pick_record(df0, ep, con, base, files)
            if rec is not None:
                return rec
        finally:
            con.close()
    except Exception:
        pass

    # 兜底：本地下载，仍然有界（最多 2 个分片）
    from huggingface_hub import hf_hub_download
    import duckdb

    def read_local(idx):
        if idx < 0 or idx >= len(files):
            return None
        local = hf_hub_download(repo_id, files[idx], repo_type="dataset")
        return duckdb.sql(f"SELECT * FROM read_parquet('{local}')").df()

    df0 = read_local(0)
    if df0 is None or df0.empty:
        return None
    if "episode_index" not in df0.columns:
        return df0.iloc[0].to_dict()
    hit = df0[df0["episode_index"] == ep]
    if not hit.empty:
        return hit.iloc[0].to_dict()
    try:
        mn, mx = int(df0["episode_index"].min()), int(df0["episode_index"].max())
        per = mx - mn + 1
        if per > 0 and len(files) > 1:
            idx = min((ep - mn) // per, len(files) - 1)
            if idx != 0:
                dfx = read_local(idx)
                if dfx is not None and "episode_index" in dfx.columns:
                    hit = dfx[dfx["episode_index"] == ep]
                    if not hit.empty:
                        return hit.iloc[0].to_dict()
    except Exception:
        pass
    return df0.iloc[0].to_dict()


def _v3_episode(repo_id: str, info: dict, ep: int, with_series: bool = True) -> dict:
    """v3.0 一集：从 meta/episodes 定位打包 mp4 的时间片（+可选曲线）。
    with_series=False 时只解析视频 URL + clip，不下载数据 parquet —— 缩略图专用，很轻。"""
    from huggingface_hub import hf_hub_download
    import duckdb
    base = f"{HF}/{repo_id}/resolve/main/"
    rec = _v3_record(repo_id, ep)
    if rec is None:
        return {"cameras": [], "series": {}, "n_frames": 0,
                "note": "未找到 meta/episodes 中该集记录，无法定位视频片段。"}

    cams = _v3_cams_from_rec(rec, info, base)

    # 曲线：定位该集的数据 parquet，按 episode_index 过滤出这一集的帧
    # （缩略图 with_series=False 时整段跳过，省掉几十 MB 的数据下载）
    series, n_frames = {}, 0
    dck = _get(rec, "data/chunk_index", "data_chunk_index")
    if dck is None:
        dck = _fuzzy(rec, "data", "chunk")
    dfi = _get(rec, "data/file_index", "data_file_index")
    if dfi is None:
        dfi = _fuzzy(rec, "data", "file")
    if with_series and dck is not None and dfi is not None:
        try:
            rel = info["data_path"].format(chunk_index=int(dck), file_index=int(dfi))
            data_url = base + rel
            df = _read_series_remote(data_url, ep)   # 远程按列/按行读，不整份下载 87MB
            if df is not None:
                if "frame_index" in df.columns:
                    df = df.sort_values("frame_index")
                n_frames = len(df)
                series = _extract_series(df)
        except Exception:
            pass
    return {"cameras": cams, "series": series, "n_frames": n_frames, "note": ""}


def _read_series_remote(data_url: str, ep: int):
    """用 duckdb httpfs 直接远程读打包 data parquet：**只取 action/state 几列 + 该集行**，
    靠 HTTP range 只拉需要的字节（几 MB），而不是把整份 87MB 下到本地。失败返回 None。"""
    import duckdb
    con = duckdb.connect()
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
        cols = [r[0] for r in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{data_url}')").fetchall()]
        if "episode_index" not in cols:
            return None
        want = [c for c in ("frame_index", "action", "observation.state") if c in cols]
        if not want:
            return None
        sel = ", ".join(f'"{c}"' for c in want)
        return con.execute(
            f"SELECT {sel} FROM read_parquet('{data_url}') "
            f"WHERE episode_index = {int(ep)}").df()
    finally:
        con.close()


def _v3_cams_from_rec(rec: dict, info: dict, base: str):
    """从一条 episode 记录解析每路相机的打包 mp4 URL + [from,to] 时间片（复用于播放与采样）。"""
    cams = []
    for vk in _video_keys(info):
        ck = _get(rec, f"videos/{vk}/chunk_index", f"{vk}/chunk_index") or _fuzzy(rec, vk, "chunk")
        fi = _get(rec, f"videos/{vk}/file_index", f"{vk}/file_index") or _fuzzy(rec, vk, "file")
        ft = _get(rec, f"videos/{vk}/from_timestamp", f"{vk}/from_timestamp")
        if ft is None:
            ft = _fuzzy(rec, vk, "from")
        tt = _get(rec, f"videos/{vk}/to_timestamp", f"{vk}/to_timestamp")
        if tt is None:
            tt = _fuzzy(rec, vk, "to_")
        if ck is None or fi is None:
            continue
        try:
            rel = info["video_path"].format(video_key=vk, chunk_index=int(ck), file_index=int(fi))
        except Exception:
            continue
        cam = {"name": _cam_name(vk), "url": base + rel}
        if ft is not None and tt is not None:
            cam["clip"] = [float(ft), float(tt)]
        cams.append(cam)
    return cams


def _even_pick(seq, n):
    """从 seq 里均匀挑 n 个（含首尾），去重保序。"""
    seq = list(seq)
    if len(seq) <= n:
        return seq
    idxs = sorted(set(round(i * (len(seq) - 1) / (n - 1)) for i in range(n)))
    return [seq[i] for i in idxs]


# ================= 采样：一次元数据读，产出 ~N 条代表性样本 =================
# 上万条轨迹不可能全展示。核心技巧：一个 meta/episodes 分片里就打包了成百上千条
# 轨迹的定位坐标，读一个分片（range 请求几十 KB）就能一次拿到十几条样本的片段坐标。

def samples(repo_id: str, n: int = 10) -> dict:
    """返回 {thumbnail, samples:[{episode, cameras:[{name,url,clip}]}]}。视频不落盘，只给坐标。"""
    info = _info(repo_id)
    if _is_packed(info):
        out = _v3_samples(repo_id, info, n)
    else:
        out = _v2_samples(repo_id, info, n)
    thumb = ""
    for s in out:
        if s.get("cameras"):
            c = s["cameras"][0]
            thumb = c["url"] + (f"#t={c['clip'][0]:.3f}" if c.get("clip") else "")
            break
    return {"thumbnail": thumb, "samples": out}


def _v2_samples(repo_id: str, info: dict, n: int) -> list:
    total = int(info.get("total_episodes", 0) or 0)
    eps = _even_pick(range(max(total, 1)), n)
    out = []
    for ep in eps:
        cams = _episode_urls(repo_id, info, ep)     # 纯拼串，不打网络
        if cams:
            out.append({"episode": int(ep), "cameras": cams})
    return out


def _v3_samples(repo_id: str, info: dict, n: int) -> list:
    """只读第一个 meta/episodes 分片（远程按列），从中均匀取 ~n 条 —— 一次 range 请求搞定。"""
    files = _v3_episode_files(repo_id)
    if not files:
        return []
    base = f"{HF}/{repo_id}/resolve/main/"
    df0 = None
    try:
        import duckdb
        con = duckdb.connect()
        try:
            con.execute("INSTALL httpfs; LOAD httpfs;")
            df0 = _read_locators_remote(con, base + files[0])
        finally:
            con.close()
    except Exception:
        df0 = None
    if df0 is None or df0.empty or "episode_index" not in df0.columns:
        # httpfs 不可用时的兜底：至少给"第 0 集"（打包首文件，无 clip 也能播）
        url = _first_video_url(repo_id, info)
        if url:
            return [{"episode": 0, "cameras": [{"name": _cam_name(_video_keys(info)[0]), "url": url}]}]
        return []
    eps = _even_pick(sorted(int(e) for e in df0["episode_index"].unique()), n)
    out = []
    for ep in eps:
        rec = df0[df0["episode_index"] == ep].iloc[0].to_dict()
        cams = _v3_cams_from_rec(rec, info, base)
        if cams:
            out.append({"episode": int(ep), "cameras": cams})
    return out


def hdf5_samples(dataset_id: str, path: str, n: int = 10) -> dict:
    """HDF5：从各 episode 组里均匀取 ~n 条，每条第一路相机作缩略图（走转码接口）。"""
    import h5py
    import urllib.parse
    if not path or not os.path.exists(path):
        return {"thumbnail": "", "samples": []}
    out = []
    try:
        with h5py.File(path, "r") as f:
            groups = _hdf5_episode_groups(f)
            picks = _even_pick(range(len(groups)), n)
            for ep in picks:
                gpath = groups[ep]
                grp = f[gpath] if gpath else f
                cam_map = _hdf5_find_cameras(grp)
                cams = [{"name": name,
                         "url": f"/api/hdf5_video/{dataset_id}?cam={urllib.parse.quote(key, safe='')}&thumb=1"}
                        for name, key in cam_map.items()]
                if cams:
                    out.append({"episode": int(ep), "cameras": cams})
    except Exception:
        return {"thumbnail": "", "samples": []}
    thumb = out[0]["cameras"][0]["url"] if out else ""
    return {"thumbnail": thumb, "samples": out}


def lerobot_episode(repo_id: str, ep: int = 0) -> dict:
    """完整一集数据。v2.x（每集一 mp4）与 v3.0（打包 + 时间片）都支持。"""
    info = _info(repo_id)
    fps = float(info.get("fps") or 0)
    total_ep = int(info.get("total_episodes", 0) or 0)

    if _is_packed(info):
        r = _v3_episode(repo_id, info, ep)
        cams = [c for c in r["cameras"] if _url_alive(c["url"])]
        return {
            "dataset_id": repo_id, "episode": ep, "fps": fps,
            "n_frames": r["n_frames"], "total_episodes": total_ep,
            "cameras": cams, "series": r["series"],
            "playable": bool(cams),
            "note": r["note"] if not cams else "",
        }

    # v2.x：每集一个 mp4
    cams = [c for c in _episode_urls(repo_id, info, ep) if _url_alive(c["url"])]
    series, n_frames, note = {}, 0, ""
    dpath = info.get("data_path")
    if dpath and "episode_index" in dpath:
        try:
            from huggingface_hub import hf_hub_download
            import duckdb
            chunks = int(info.get("chunks_size", 1000) or 1000)
            rel = _fmt(dpath, episode_chunk=ep // chunks, episode_index=ep)
            local = hf_hub_download(repo_id, rel, repo_type="dataset")
            df = duckdb.sql(f"SELECT * FROM read_parquet('{local}')").df()
            if "frame_index" in df.columns:
                df = df.sort_values("frame_index")
            n_frames = len(df)
            series = _extract_series(df)
        except Exception as e:
            note = f"曲线读取失败：{type(e).__name__}"

    return {
        "dataset_id": repo_id, "episode": ep, "fps": fps,
        "n_frames": n_frames, "total_episodes": total_ep,
        "cameras": cams, "series": series,
        "playable": bool(cams), "note": note,
    }


# ==================================================================
# HDF5 提取器（机构自定义格式）
# ==================================================================
# 与 LeRobot 的关键区别：视频不在任何 CDN 上，帧就存在 .h5 文件里。
# 所以后端要**读帧 → 按需转码成小 mp4（缓存）→ 自己把字节喂给 <video>**。
# 前端播放器不变：它只认 cameras[].url，url 指向我们自己的 /api/hdf5_video 即可。
#
# 布局千差万别，做启发式，覆盖两种最常见的：
#   robomimic：data/demo_0, demo_1 ... 每个 demo 下 obs/<cam>_image + actions
#   ALOHA/ACT：/observations/images/<cam> + /action + /observations/qpos（单文件=单集）
# 都不匹配时走 generic：全文件扫 (T,H,W,3) 的数组当相机。

import os
import hashlib
import tempfile

_VIZ_CACHE = os.path.join(tempfile.gettempdir(), "mdh_viz_cache")


def _is_image_ds(shape, dtype):
    """判断一个数据集像不像"一段视频帧" (T,H,W,C) 或 (T,H,W) 灰度。"""
    import numpy as np
    if len(shape) == 4 and shape[0] > 1 and shape[-1] in (1, 3) and shape[1] >= 8 and shape[2] >= 8:
        return True
    if len(shape) == 3 and shape[0] > 1 and shape[1] >= 16 and shape[2] >= 16 and dtype == np.uint8:
        return True
    return False


def _hdf5_episode_groups(f):
    """返回该文件里"每一集"对应的组路径列表（robomimic 是各 demo；aloha/generic 是根 ['']）。"""
    import h5py
    if "data" in f and isinstance(f["data"], h5py.Group):
        demos = [k for k in f["data"].keys() if k.startswith(("demo", "episode", "traj"))]
        if demos:
            # 自然排序 demo_2 < demo_10
            demos.sort(key=lambda s: int("".join(ch for ch in s if ch.isdigit()) or 0))
            return [f"data/{k}" for k in demos]
    return [""]


def _hdf5_find_cameras(grp):
    """在一个组里递归找相机数据集，返回 {显示名: 绝对h5路径}。"""
    import h5py
    cams = {}

    def visit(name, obj):
        if isinstance(obj, h5py.Dataset) and _is_image_ds(obj.shape, obj.dtype):
            disp = name.split("/")[-1]
            cams[disp] = obj.name        # obj.name 是文件内绝对路径

    grp.visititems(visit)
    return cams


def _hdf5_find_series(grp):
    """在一个组里找 action / state 数组，返回 (action绝对路径, state绝对路径)。"""
    import h5py
    action = state = None

    def visit(name, obj):
        nonlocal action, state
        if not isinstance(obj, h5py.Dataset) or obj.ndim < 1:
            return
        leaf = name.split("/")[-1].lower()
        if action is None and leaf in ("action", "actions") and obj.ndim >= 2:
            action = obj.name
        if state is None and leaf in ("qpos", "state", "joint_positions", "ee_pose", "robot_state"):
            state = obj.name

    grp.visititems(visit)
    return action, state


def _hdf5_fps(f, grp):
    for src in (grp, f):
        try:
            for k in ("fps", "frame_rate", "control_freq"):
                if k in src.attrs:
                    return float(src.attrs[k])
        except Exception:
            pass
    return 20.0


def _series_from_h5(f, action_key, state_key, max_dims=12, max_points=300):
    import numpy as np
    out = {}
    for key, short in ((action_key, "action"), (state_key, "state")):
        if not key or key not in f:
            continue
        arr = np.asarray(f[key])
        if arr.ndim == 1:
            arr = arr[:, None]
        n = arr.shape[0]
        if n == 0:
            continue
        step = max(1, n // max_points)
        idx = list(range(0, n, step))
        width = min(arr.shape[1], max_dims)
        for d in range(width):
            out[f"{short}[{d}]"] = [float(arr[i, d]) for i in idx]
    return out


def _to_uint8_rgb(fr, max_w=640):
    """把一帧规整成浏览器能编码的 uint8 RGB，必要时降采样。"""
    import numpy as np
    fr = np.asarray(fr)
    if fr.ndim == 2:                      # 灰度 -> 三通道
        fr = np.stack([fr] * 3, axis=-1)
    if fr.ndim == 3 and fr.shape[-1] == 1:
        fr = np.repeat(fr, 3, axis=-1)
    if fr.dtype != np.uint8:              # 浮点 [0,1] 或其它 -> 0..255
        mx = float(fr.max()) if fr.size else 1.0
        fr = (fr * (255.0 if mx <= 1.0 else 1.0)).clip(0, 255).astype("uint8")
    h, w = fr.shape[:2]
    if w > max_w:                         # 按整数步长降采样（免依赖 PIL）
        fac = (w + max_w - 1) // max_w
        fr = fr[::fac, ::fac]
    return fr[:, :, :3]


def _cache_key(*parts):
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:16]
    return h


def hdf5_video_file(path: str, cam_key: str, thumb: bool = False) -> str:
    """把 h5 里某路相机转码成 mp4（缓存），返回 mp4 文件路径。"""
    import h5py
    import imageio
    max_frames = 120 if thumb else 500
    max_w = 240 if thumb else 640
    mtime = os.path.getmtime(path)
    os.makedirs(_VIZ_CACHE, exist_ok=True)
    out = os.path.join(_VIZ_CACHE, _cache_key(path, mtime, cam_key, thumb) + ".mp4")
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out

    with h5py.File(path, "r") as f:
        ds = f[cam_key]
        T = ds.shape[0]
        step = max(1, T // max_frames)
        fps = _hdf5_fps(f, ds.parent)
        w = imageio.get_writer(
            out, fps=max(1, int(fps)), codec="libx264", macro_block_size=16,
            pixelformat="yuv420p", ffmpeg_params=["-movflags", "+faststart"])
        try:
            for i in range(0, T, step):
                w.append_data(_to_uint8_rgb(ds[i], max_w))
        finally:
            w.close()
    return out


def hdf5_episode(dataset_id: str, path: str, ep: int = 0) -> dict:
    """完整一集：相机（指向我们自己的转码接口）+ 曲线。"""
    import h5py
    if not path or not os.path.exists(path):
        return {"playable": False,
                "reason": "本机找不到该 HDF5 文件（机构数据集需在运行后端的机器上可读）。"}
    with h5py.File(path, "r") as f:
        groups = _hdf5_episode_groups(f)
        total = len(groups)
        ep = max(0, min(ep, total - 1))
        gpath = groups[ep]
        grp = f[gpath] if gpath else f
        cam_map = _hdf5_find_cameras(grp)
        action_key, state_key = _hdf5_find_series(grp)
        fps = _hdf5_fps(f, grp)
        n_frames = 0
        if cam_map:
            first = next(iter(cam_map.values()))
            n_frames = int(f[first].shape[0])
        series = _series_from_h5(f, action_key, state_key)

    import urllib.parse
    cams = [{
        "name": name,
        "url": f"/api/hdf5_video/{dataset_id}?cam={urllib.parse.quote(key, safe='')}",
    } for name, key in cam_map.items()]

    return {
        "dataset_id": dataset_id, "episode": ep, "fps": fps,
        "n_frames": n_frames, "total_episodes": total,
        "cameras": cams, "series": series,
        "playable": bool(cams),
        "note": "" if cams else "未在该 HDF5 中识别到相机帧数据。",
    }


def hdf5_preview(dataset_id: str, path: str) -> dict:
    """卡片缩略图：第 0 集第一路相机的转码视频（低分辨率、少帧）。"""
    import h5py
    if not path or not os.path.exists(path):
        return {}
    try:
        with h5py.File(path, "r") as f:
            groups = _hdf5_episode_groups(f)
            grp = f[groups[0]] if groups[0] else f
            cam_map = _hdf5_find_cameras(grp)
        if not cam_map:
            return {}
        key = next(iter(cam_map.values()))
        import urllib.parse
        return {"video": f"/api/hdf5_video/{dataset_id}?cam={urllib.parse.quote(key, safe='')}&thumb=1",
                "name": next(iter(cam_map.keys()))}
    except Exception:
        return {}
