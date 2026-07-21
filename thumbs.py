"""
截图缓存（选择性缓存 / preview_sample_ref）
==============================================

每个数据集在服务器上缓存**几张小截图**：用 ffmpeg 从视频只读前几秒抽 3~4 帧、
缩到 ~360px 存成 JPEG（每张几十 KB）。这样：
  - 画廊直接读本地图，**秒开**，不用每次去 HF 拉视频；
  - 用户按图快速判断内容，确认要看再跳转完整回放；
  - 存储极小（几张 JPEG × 上百数据集 ≈ 十几 MB），符合"缓存一点、不占大存储"。

缓存目录默认落在已挂载的 viz_cache 下（/tmp/mdh_viz_cache/thumbs → 宿主 /data/viz_cache/thumbs），
所以**不用改 docker-compose**。国内服务器抽帧走 HF 镜像（读 HF_ENDPOINT）。
"""

import os
import glob
import hashlib
import tempfile
import subprocess

_THUMB_DIR = os.environ.get(
    "MDH_THUMB_DIR",
    os.path.join(tempfile.gettempdir(), "mdh_viz_cache", "thumbs"))
_HF_MIRROR = os.environ.get("HF_ENDPOINT", "").strip().rstrip("/")


def _mirror(url: str) -> str:
    if _HF_MIRROR and url and "huggingface.co" in url:
        return url.replace("huggingface.co", _HF_MIRROR.split("://", 1)[-1])
    return url


def _key(dataset_id: str) -> str:
    return hashlib.md5(dataset_id.encode()).hexdigest()[:16]


def dir_for(dataset_id: str) -> str:
    return os.path.join(_THUMB_DIR, _key(dataset_id))


def cached_files(dataset_id: str):
    """已缓存的截图文件路径（按名排序）。没有则空列表。"""
    d = dir_for(dataset_id)
    return sorted(glob.glob(os.path.join(d, "*.jpg"))) if os.path.isdir(d) else []


def has_cache(dataset_id: str) -> bool:
    return len(cached_files(dataset_id)) > 0


def extract(dataset_id: str, video_url: str, seconds: int = 4, width: int = 360) -> int:
    """从视频前 seconds 秒抽 1 帧/秒（约 seconds 张），缩放存 JPEG。返回缓存到的张数。
    一次 ffmpeg 调用、只读开头几秒（HTTP range），高效；失败静默返回 0。"""
    if not video_url:
        return 0
    try:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 0
    url = _mirror(video_url)
    d = dir_for(dataset_id)
    os.makedirs(d, exist_ok=True)
    pattern = os.path.join(d, "%d.jpg")
    try:
        subprocess.run(
            [ff, "-y", "-i", url, "-t", str(seconds),
             "-vf", f"fps=1,scale={width}:-1", "-q:v", "6", pattern],
            timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    # 清掉 0 字节的坏帧
    for f in cached_files(dataset_id):
        try:
            if os.path.getsize(f) == 0:
                os.remove(f)
        except Exception:
            pass
    return len(cached_files(dataset_id))
