"""
迷你 DataHub —— 网页界面（Streamlit）
======================================

一个让 hub "好用起来"的网页：搜索、筛选、看统计、看数据集详情、一键在线可视化。
所有数据来自 catalog.duckdb（首次运行会自动灌入样例数据）。

运行：
    pip install -r requirements.txt
    streamlit run app.py

然后浏览器会自动打开 http://localhost:8501
"""

import streamlit as st
import hub_data as hd

st.set_page_config(page_title="机器人 DataHub", page_icon="🤖", layout="wide")

# ---------------- 全站样式美化 ----------------
st.markdown("""
<style>
/* 收紧顶部留白 */
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1300px; }

/* 渐变标题横幅 */
.hero {
    background: linear-gradient(110deg, #4F46E5 0%, #7C3AED 55%, #2563EB 100%);
    border-radius: 16px; padding: 26px 32px; margin-bottom: 22px;
    color: #fff; box-shadow: 0 8px 24px rgba(79,70,229,.22);
}
.hero h1 { color:#fff; font-size: 1.9rem; margin:0 0 6px 0; font-weight:700; }
.hero p  { color: #E0E7FF; margin:0; font-size: 1.02rem; }

/* 指标做成卡片 */
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #EAECF3; border-radius: 12px;
    padding: 14px 18px; box-shadow: 0 1px 3px rgba(16,24,40,.05);
}
[data-testid="stMetricLabel"] { color:#667085; font-weight:600; }
/* 数值字号自适应缩小 + 允许换行，避免长名字（如 single_arm）被截断 */
[data-testid="stMetricValue"] {
    color:#1F2937; font-weight:700;
    font-size: clamp(1.05rem, 1.6vw, 1.5rem);
    white-space: normal; overflow-wrap: anywhere; line-height: 1.25;
}
[data-testid="stMetricValue"] > div { white-space: normal; overflow: visible; }

/* 章节小标题 */
h2, h3 { color:#1F2937; font-weight:700; }

/* 按钮圆角 + 悬停 */
.stButton > button, .stLinkButton > a {
    border-radius: 10px; font-weight:600; border:1px solid #E5E7EB;
}
.stButton > button:hover { border-color:#4F46E5; color:#4F46E5; }

/* 侧栏标题 */
[data-testid="stSidebar"] h2 { font-size:1.1rem; }
[data-testid="stSidebar"] { border-right:1px solid #EEF0F5; }

/* 数据表圆角 */
[data-testid="stDataFrame"] { border-radius: 10px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# 连接数据库（缓存，避免每次刷新都重连）
@st.cache_resource
def get_con():
    return hd.ensure_catalog()

try:
    con = get_con()
except Exception as e:
    if "lock" in str(e).lower():
        st.error(
            "⚠️ 数据库被另一个程序占用——通常是有旧的网页或脚本还在后台运行。\n\n"
            "请在终端运行 `pkill -f streamlit` 关闭所有旧实例，再重新启动本网页。"
        )
        st.stop()
    raise

st.markdown("""
<div class="hero">
  <h1>🤖 机器人 DataHub</h1>
  <p>跨源聚合 · 统一检索 · 自动质检 · 一键回放 —— 具身智能数据的联邦门户</p>
</div>
""", unsafe_allow_html=True)

# ---------------- 顶部指标卡 ----------------
stats = hd.summary_stats(con)
c1, c2, c3 = st.columns(3)
c1.metric("数据集数量", stats["n_datasets"])
c2.metric("轨迹总数", f'{stats["n_episodes"]:,}')
c3.metric("总帧数", f'{stats["n_frames"]:,}')

# ---------------- 侧栏筛选 ----------------
st.sidebar.header("🔎 筛选")
search = st.sidebar.text_input("搜索名称 / ID", "")
embodiments = st.sidebar.multiselect("本体类型", hd.distinct_values(con, "embodiment"))
formats = st.sidebar.multiselect("源格式", hd.distinct_values(con, "source_format"))
provenances = st.sidebar.multiselect("采集方式", hd.distinct_values(con, "provenance_type"),
                                     help="teleop 遥操作 / sim 仿真 / human_video 人类视频 等")
commercial_only = st.sidebar.checkbox("仅可商用", help="自动排除 CC-BY-NC 等非商用许可")
failures_only = st.sidebar.checkbox("仅含失败标注", help="带失败数据的数据集更有训练价值")
min_episodes = st.sidebar.slider("最少轨迹数", 0, 500, 0, step=10)
min_quality = st.sidebar.slider("最低质量分", 0.0, 1.0, 0.0, step=0.05,
                                help="入库自动质检打分；运行 05_profile_quality.py 生成")

df = hd.query_datasets(
    con, search=search, embodiments=embodiments, formats=formats, provenances=provenances,
    commercial_only=commercial_only, failures_only=failures_only,
    min_episodes=min_episodes, min_quality=min_quality,
)

# ---------------- 主区：两栏 ----------------
left, right = st.columns([2, 1])

with left:
    st.subheader(f"数据集（{len(df)} 个）")
    show_cols = ["name", "embodiment", "robot_model", "provenance_type", "source_format",
                 "license_spdx", "commercial_ok", "quality_score", "learnability_score",
                 "n_episodes", "fps", "n_cameras", "has_failure_labels"]
    df_show = df[show_cols].copy()
    # 未评分(-1)/未知(0) 的数值留空显示，避免刺眼的 -1 / 0
    df_show.loc[df_show["quality_score"] < 0, "quality_score"] = None
    df_show.loc[df_show["learnability_score"] < 0, "learnability_score"] = None
    df_show.loc[df_show["fps"] <= 0, "fps"] = None
    df_show.loc[df_show["n_cameras"] <= 0, "n_cameras"] = None
    st.dataframe(
        df_show,
        use_container_width=True, hide_index=True,
        column_config={
            "name": "名称", "embodiment": "本体", "robot_model": "机器人",
            "provenance_type": "采集方式", "source_format": "格式",
            "license_spdx": "许可证", "commercial_ok": "可商用",
            "quality_score": "质量分", "learnability_score": "可学性",
            "n_episodes": "轨迹数", "fps": "频率", "n_cameras": "摄像头",
            "has_failure_labels": "含失败",
        },
    )

with right:
    st.subheader("按本体分布")
    emb_df = hd.by_embodiment(con)
    if not emb_df.empty:
        st.bar_chart(emb_df, x="embodiment", y="episodes", height=260)

# ---------------- 数据集详情 ----------------
st.divider()
st.subheader("📂 数据集详情")

if len(df) == 0:
    st.info("没有符合条件的数据集，试着放宽左侧筛选条件。")
else:
    picked = st.selectbox("选择一个数据集查看详情", df["dataset_id"].tolist())
    row = df[df["dataset_id"] == picked].iloc[0]

    import json
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("本体", f'{row["embodiment"]} ({int(row["dof"])} DOF)')
    d2.metric("轨迹数", int(row["n_episodes"]))
    d3.metric("采集方式", row["provenance_type"] or "—")
    d4.metric("可商用", "是" if row["commercial_ok"] else "否")

    st.write(f"**许可证：** `{row['license_spdx']}`　|　**可再分发：** "
             f"{'是' if row['redistribute_ok'] else '否'}　|　**源格式：** `{row['source_format']}`　"
             f"|　**来源：** {row['source']}")
    if not row["commercial_ok"]:
        st.warning("⚠️ 该数据集**不可商用**，请勿混入商业训练集。")

    # 质检分（B4 自动质检）
    q, l = row["quality_score"], row["learnability_score"]
    if q is not None and q >= 0:
        st.write(f"**质量分：** {q:.2f}　|　**可学性：** {l:.2f}　"
                 f"<span style='color:gray'>（入库自动质检 B4）</span>", unsafe_allow_html=True)
    else:
        st.caption("质量分：未评分（运行 `python 05_profile_quality.py` 生成）")

    # 动作约定（文档 4.3：只描述不强转）+ taxonomy 标签
    try:
        ac = json.loads(row["action_convention"]) if row["action_convention"] else {}
    except Exception:
        ac = {}
    if ac:
        st.write("**动作约定：** " + "　".join(f"`{k}={v}`" for k, v in ac.items()))
    for label, col in [("任务", "tasks"), ("场景", "scenes"), ("模态", "modalities")]:
        try:
            vals = json.loads(row[col]) if row[col] else []
        except Exception:
            vals = []
        if vals:
            st.write(f"**{label}：** " + "　".join(f"`{v}`" for v in vals))

    # 回放（本地弹出 Rerun）+ 在线可视化 + 主页链接
    b1, b2, b3 = st.columns(3)
    if b1.button("▶ 在 Rerun 中回放", help="点一下，从门户直接打开这个数据集的回放窗口"):
        try:
            import viz
            from demo import make_demo_episode
            ep = make_demo_episode(dof=int(row["dof"]) or 7, fps=float(row["fps"]) or 30.0,
                                   task_text=f"{row['name']} ({row['source_format']})")
            viz.log_unified([{
                "name": str(row["name"]).replace(" ", "_"),
                "source_format": row["source_format"],
                "canon": ep,
            }], title=f"replay_{picked}")
            st.success("已弹出 Rerun 回放窗口（合成示例数据；真实数据接入后回放真实轨迹）。")
        except Exception as e:
            st.error(f"回放启动失败：{e}（确认已 pip install rerun-sdk）")
    if row["source"] == "huggingface" or "lerobot" in str(row["source_format"]):
        b2.link_button("🎬 在线可视化", hd.hf_visualizer_url(picked))
    if row["homepage"]:
        b3.link_button("🔗 数据集主页", row["homepage"])

    # 轨迹列表
    st.markdown("**轨迹样例：**")
    ep_df = hd.get_episodes(con, picked)
    if ep_df.empty:
        st.caption("（该数据集还没有登记轨迹级元数据）")
    else:
        st.dataframe(ep_df, use_container_width=True, hide_index=True)

st.sidebar.divider()
st.sidebar.caption("数据来自 catalog.duckdb。\n"
                   "用 `python 03_ingest_real_lerobot.py <repo_id>` 可接入真实数据集。")
