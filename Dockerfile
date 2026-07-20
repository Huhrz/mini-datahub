# 后端镜像：FastAPI + 摄入 + 语义搜索（核心依赖，无 lerobot 冲突）
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（利用 Docker 层缓存）
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
