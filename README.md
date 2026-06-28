# 迷你 DataHub —— 初步成果脚手架

一条"端到端走通"的细线，演示 DataHub 的三个核心点：**统一格式 → 元数据目录检索 → 可视化预览**。
可以**先不下载任何数据**就跑通（用内置合成 demo），再换成真实 LeRobot 数据集。

## 文件说明

| 文件 | 作用 |
|---|---|
| `schema.py` | **联邦目录项 Schema（项目核心资产）**。已对齐系统设计文档 v0.1 第 4.1 节的 Catalog Entry：含 `action_convention`（动作约定，只描述不强转，见文档 4.3）、`provenance_type`（采集方式）、taxonomy 标签（tasks/scenes/modalities）、细化的 license（spdx/可商用/可再分发）、quality_score、lineage 等。建表/插入语句从字段定义**自动生成**，加字段不会出错。 |
| `demo.py` | 合成示例数据生成器，让你不联网也能跑通整条线。 |
| `01_explore_and_visualize.py` | 步骤 1：加载一条轨迹，用 **Rerun** 可视化（摄像头画面 + 关节曲线）。 |
| `02_build_catalog.py` | 步骤 2：把元数据写进 **DuckDB**，跑示例检索（按本体 / 许可 / 失败标注筛选）。 |
| `03_ingest_real_lerobot.py` | 步骤 2.5：接入**真实** LeRobot 数据集——只拉几 KB 的 `meta/info.json` 就登记进目录（演示"元数据先行、原始数据按需取"）。需联网。 |
| `04_convert_formats.py` | 步骤 3：**粘合层**——用适配器把 LeRobot 式 / RLDS 式两种异构格式归一成同一种规范表示，并对归一结果**自动质检**。不联网即可跑。 |
| `quality.py` | **质检引擎（B4）**：在统一表示上算质量分 / 可学性分，分数可解释。格式无关，入库时复用同一套。 |
| `05_profile_quality.py` | 步骤 4：**入库自动质检 demo**——造 good/lazy/dirty 三种轨迹证明引擎能区分好坏，并把分数写回目录。不联网即可跑。 |
| `06_profile_real.py` | 步骤 4.5：对**真实**数据集采样质检并写回（落地扩展第 1、2 条）。需联网 + `pip install lerobot`。 |
| `07_check_links.py` | 步骤 5：**联邦指针健康检查**——扫描所有数据集主页链接，标出失效(404)的（对应文档第 8 章"联邦指针失效"风险）。需联网，只用标准库。 |
| `hub_data.py` | **数据层**：网页和命令行共用的目录读写逻辑（连接 DuckDB、查询、筛选、统计）。不依赖界面，可单测。 |
| `app.py` | **网页界面（Streamlit）**：搜索、筛选、统计图、数据集详情、一键在线可视化。让 hub 真正"好用起来"。 |
| `requirements.txt` | 依赖。 |

## 🌐 启动网页（最推荐的演示方式）

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。你会看到：
- 顶部统计卡（数据集数 / 轨迹数 / 帧数）
- 左侧筛选栏（搜索、本体、格式、仅可商用、仅含失败标注、最少轨迹数）
- 数据集列表 + 按本体分布的柱状图
- 选中某数据集看详情，点"🎬 在线可视化"直接跳到 Rerun 网页查看器

首次运行会自动用样例数据填充目录。想换成真实数据，先跑 `03_ingest_real_lerobot.py` 再刷新网页即可。
按 `Ctrl + C` 停止网页服务。

## 快速开始（3 步）

```bash
# 1. 装依赖
pip install -r requirements.txt

# 2. 可视化一条合成轨迹（会自动弹出 Rerun 窗口）
python 01_explore_and_visualize.py

# 3. 建目录并检索（终端打印查询结果）
python 02_build_catalog.py

# 4. 演示"粘合层"：把两种异构格式归一（不联网）
python 04_convert_formats.py

# 5. 演示"入库自动质检"：给好/坏数据打分并写回目录（不联网）
python 05_profile_quality.py
```

## 跑真实数据（需联网）

```bash
# A. 接入真实数据集的元数据到目录（只下载几 KB，很快）
python 03_ingest_real_lerobot.py lerobot/pusht lerobot/aloha_sim_insertion_human
python 02_build_catalog.py   # 可再跑检索看效果（注：02 会重建表，真实接入请保留 03 的写入）

# B. 可视化真实数据集的一条轨迹（需 pip install lerobot，下载较大）
python 01_explore_and_visualize.py --repo-id lerobot/aloha_sim_insertion_human --episode 0
```

> 提示：`02_build_catalog.py` 每次会 DROP 重建表（仅为演示）。若想保留 `03` 接入的真实数据，
> 把 `02` 开头的 `DROP TABLE` 那行去掉即可。

## 这份脚手架演示了什么（给导师看的话术）

1. **统一格式的思路**：所有数据集无论来源（LeRobot / RLDS / HDF5），都抽取成同一张元数据 schema —— 这就是"格式统一"在元数据层的落地。
2. **元数据是发动机**：`02_build_catalog.py` 的 6 条查询证明，有了好 schema，就能做"只要可商用的""只要双臂的""找所有失败轨迹"——这些正是 DataHub 比普通网盘强的地方。
3. **可视化复用现成轮子**：`01` 直接用 Rerun，不自研播放器。

## 下一步可以扩展的方向

- 把 `demo.py` 换成真实 `LeRobotDataset`，让 `02` 从真实数据抽元数据填 schema。
- 接入第二个**不同格式**（RLDS）的数据集，用 `openx2lerobot` / `forge` 转换后入库，真正演示"粘合层"。
- 给 schema 增加"数据质量分 / 可学性分"字段，做成入库时自动质检。
- 把 `lerobot-dataset-visualizer` 网页组件嵌进一个简单的 web 页面，做成真正的 hub 界面。
