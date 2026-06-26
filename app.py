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

# 连接数据库（缓存，避免每次刷新都重连）
@st.cache_resource
def get_con():
    return hd.ensure_catalog()

con = get_con()

st.title("🤖 机器人 DataHub")
st.caption("一个聚合、检索、预览机器人学习数据集的迷你枢纽")

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
commercial_only = st.sidebar.checkbox("仅可商用", help="自动排除 CC-BY-NC 等非商用许可")
failures_only = st.sidebar.checkbox("仅含失败标注", help="带失败数据的数据集更有训练价值")
min_episodes = st.sidebar.slider("最少轨迹数", 0, 500, 0, step=10)

df = hd.query_datasets(
    con, search=search, embodiments=embodiments, formats=formats,
    commercial_only=commercial_only, failures_only=failures_only, min_episodes=min_episodes,
)

# ---------------- 主区：两栏 ----------------
left, right = st.columns([2, 1])

with left:
    st.subheader(f"数据集（{len(df)} 个）")
    show_cols = ["name", "embodiment", "robot_model", "source_format",
                 "license", "commercial_use", "n_episodes", "fps",
                 "n_cameras", "has_failure_labels"]
    st.dataframe(
        df[show_cols],
        use_container_width=True, hide_index=True,
        column_config={
            "name": "名称", "embodiment": "本体", "robot_model": "机器人",
            "source_format": "格式", "license": "许可证", "commercial_use": "可商用",
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

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("本体", row["embodiment"])
    d2.metric("轨迹数", int(row["n_episodes"]))
    d3.metric("频率(fps)", row["fps"])
    d4.metric("可商用", "是" if row["commercial_use"] else "否")

    st.write(f"**许可证：** `{row['license']}`　|　**源格式：** `{row['source_format']}`　"
             f"|　**来源：** {row['source']}")
    if not row["commercial_use"]:
        st.warning("⚠️ 该数据集**不可商用**，请勿混入商业训练集。")

    # 在线可视化 + 主页链接
    b1, b2 = st.columns(2)
    if row["source"] == "huggingface" or "lerobot" in str(row["source_format"]):
        b1.link_button("🎬 在线可视化这个数据集", hd.hf_visualizer_url(picked))
    if row["homepage"]:
        b2.link_button("🔗 数据集主页", row["homepage"])

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
