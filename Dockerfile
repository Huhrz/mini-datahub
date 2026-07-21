# 后端镜像：FastAPI + 摄入 + 语义搜索 + 截图抽帧
# 国内服务器：pip 与 apt 都走阿里云镜像（同厂内网，快且稳）
FROM python:3.11-slim

WORKDIR /app

# 先装 Python 依赖（利用层缓存）；pip 走阿里云镜像 + 大超时/多重试（torch 很大）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
        -i https://mirrors.aliyun.com/pypi/simple --timeout 120 --retries 10 && \
    pip install --no-cache-dir -r requirements.txt \
        -i https://mirrors.aliyun.com/pypi/simple --timeout 120 --retries 10

# 系统 ffmpeg（截图抽帧用；比 imageio 静态版稳，支持 HTTPS + av1）；apt 走阿里云 debian 源
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi && \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 再拷代码（改代码只重建这层，不重装依赖）
COPY . .

ENV MDH_DB=/data/catalog.duckdb
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
