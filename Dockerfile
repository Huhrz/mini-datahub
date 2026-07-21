# 后端镜像：FastAPI + 摄入 + 语义搜索（核心依赖，无 lerobot 冲突）
FROM python:3.11-slim

WORKDIR /app

# 系统 ffmpeg（截图抽帧用；比 imageio 自带的静态 ffmpeg 稳，支持 HTTPS + av1）
# apt 走阿里云镜像（服务器在阿里云，内网快）
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 Docker 层缓存）；国内走清华 PyPI 镜像
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 再拷代码
COPY . .

# 目录数据库放到挂卷目录，容器重启不丢
ENV MDH_DB=/data/catalog.duckdb
VOLUME ["/data"]

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
