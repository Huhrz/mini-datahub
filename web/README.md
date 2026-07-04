# 机器人 DataHub —— React 前端

精致版网页（Vite + React + Tailwind），通过 API 从 FastAPI 后端拿数据。
前后端分离：后端逻辑不变，前端可随意迭代设计（也可对接 Claude Design）。

## 架构

```
浏览器 (React :5173)  ──/api──▶  FastAPI (:8000)  ──▶  hub_data.py / DuckDB
```

## 怎么跑（要开两个终端）

**终端 1 —— 启动后端 API：**
```bash
cd ~/Desktop/RoboticDataHub/mini_datahub
pip3 install fastapi uvicorn
uvicorn api:app --reload --port 8000
```
（可打开 http://localhost:8000/docs 交互测试接口）

**终端 2 —— 启动前端：**
```bash
cd ~/Desktop/RoboticDataHub/mini_datahub/web
npm install        # 首次需要，装 node 依赖
npm run dev
```
浏览器打开终端里显示的地址（通常 http://localhost:5173）。

> 需要先装 Node.js（https://nodejs.org ，装 LTS 版即可，附带 npm）。

## 功能

- 顶部渐变横幅 + 统计卡
- 侧栏筛选：搜索、任务概念（taxonomy）、本体、格式、采集方式、仅可商用、仅含失败、最低质量分
- 数据集卡片列表 → 点开右侧详情抽屉（含动作约定、任务/场景/模态标签、在线可视化/主页）
- **覆盖度地图**标签页：本体 × 任务概念热力图，一眼看数据分布与空白(gap)

## 文件

- `src/App.jsx` — 主界面（统计卡 / 筛选 / 列表 / 详情抽屉 / 标签页）
- `src/CoverageHeatmap.jsx` — 覆盖度热力图
- `src/api.js` — 与后端通信的封装
- `vite.config.js` — 开发代理（把 /api 转发到 :8000）
