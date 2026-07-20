#!/usr/bin/env bash
# 一键创建隔离的虚拟环境并装好核心依赖（解决 sentence-transformers/lerobot 冲突）
# 用法：  bash setup.sh
set -e

cd "$(dirname "$0")"
echo "==> 创建虚拟环境 .venv"
python3 -m venv .venv

echo "==> 安装核心依赖（干净环境，无 lerobot 冲突）"
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo ""
echo "✅ 完成。以后所有命令都在这个环境里跑："
echo ""
echo "   source .venv/bin/activate      # 进入环境（提示符会出现 (.venv)）"
echo "   uvicorn api:app --reload --port 8000    # 启动后端"
echo "   python 11_batch_ingest.py --limit 200   # 接入数据"
echo "   deactivate                     # 退出环境"
echo ""
echo "（前端另开一个终端： cd web && npm install && npm run dev）"
