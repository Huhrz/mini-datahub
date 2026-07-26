# 后端镜像：FastAPI + 摄入 + 语义搜索 + 截图抽帧
# 关键：装 CPU 版 torch（服务器无 GPU），镜像小 2-3GB、下载快，避免 CUDA 库白占盘。
# 国内：pip/apt 走阿里云镜像；torch 走官方 CPU 索引。
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
        -i https://mirrors.aliyun.com/pypi/simple --timeout 120 --retries 10 && \
    pip install --no-cache-dir torch \
        --index-url https://download.pytorch.org/whl/cpu --timeout 180 --retries 10 && \
    pip install --no-cache-dir -r requirements.txt \
        -i https://mirrors.aliyun.com/pypi/simple --timeout 120 --retries 10

# 系统 ffmpeg（截图抽帧）；apt 走阿里云 debian 源
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi && \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY . .

ENV MDH_DB=/data/catalog.duckdb
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
