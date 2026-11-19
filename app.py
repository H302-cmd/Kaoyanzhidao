"""研途AI - 考研全周期智能助手（Streamlit 网页应用）。

运行：streamlit run app.py
若未配置 .env，自动进入「离线演示模式」，全部功能可用。
"""
import sys
import json
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from src import recommender, planner, qa, rag

st.set_page_config(page_title="研途AI · 考研规划助手", page_icon="🎓", layout="wide")

# 加载动态选项（专业 / 地区）
_UNIVERSITIES = rag.load_universities()
MAJORS = sorted({r["专业"] for r in _UNIVERSITIES})
REGIONS = sorted({r["省份"] for r in _UNIVERSITIES})
with open(config.DATA_DIR / "policies.json", encoding="utf-8") as _f:
    POLICIES = json.load(_f)


# ---------- 侧边栏 ----------
with st.sidebar:
    st.markdown("# 研途AI")
    st.caption("考研全周期智能规划助手")
    st.markdown("---")

    mode = "🟢 真实大模型模式" if config.is_live_mode() else "🟡 离线演示模式"
    st.info(f"当前运行：**{mode}**")
    if not config.is_live_mode():
        st.caption("配置 .env 中的 API Key 即可切换到真实大模型模式")

    st.markdown("---")
    st.subheader("个人考研档案")
    background = st.text_input("本科背景", "双非本科")
    target_score = st.number_input("目标分数", min_value=150, max_value=500, value=350)
    region = st.selectbox("意向地区", ["不限"] + REGIONS)
    st.caption(f"院校库覆盖 {len(MAJORS)} 个专业 · {len(REGIONS)} 个省级地区")

    st.markdown("---")
    st.caption("数据为示例，请以官方招生简章为准")


# ---------- 主体 ----------
st.title("考研路上，让 AI 陪你做对每一个决定")
st.caption("智能择校 · 备考计划 · 政策问答 —— 基于真实数据检索 + 大模型生成")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 智能择校", "📅 备考计划", "📚 政策问答", "🏫 院校数据库"])


# ===== 功能1：智能择校 =====
with tab1:
    st.header("智能择校规划")
    st.write("根据你的分数与偏好，从院校库检索匹配院校，并按「冲/稳/保」分档。")
    major = st.selectbox("报考专业", MAJORS, key="major1")
    preference = st.text_input(
        "其他偏好（可选）", "想留在意向地区发展", key="pref1",
        help="在这里写明地区（如「浙江」「杭州」「长三角」）会优先于上方「意向地区」筛选；支持多个地区，如「浙江或江苏」。",
    )
    st.caption("💡 提示：在「其他偏好」里写地区（如 浙江 / 杭州 / 长三角），将优先按该地区筛选；留默认则按侧边栏「意向地区」。")
    if st.button("生成择校方案", type="primary", key="btn_rec"):
        profile = {
            "major": major,
            "background": background,
            "target_score": target_score,
            "region": region,
            "preference": preference,
        }
        with st.spinner("正在检索院校库并分析..."):
            result = recommender.recommend(profile)
        st.markdown("---")
        st.markdown(result)


# ===== 功能2：备考计划 =====
with tab2:
    st.header("个性化备考计划生成")
    st.write("输入目标与时间投入，生成含三阶段规划、月度任务、一周时间表、自检清单的详细备考计划。")
    col1, col2 = st.columns(2)
    with col1:
        target_school = st.text_input("目标院校专业", "浙江大学 计算机科学与技术")
        subjects = st.text_input("初试科目", "政治/英语一/数学一/数据结构")
        weak = st.selectbox("薄弱科目", ["数学", "英语", "政治", "专业课", "无"])
    with col2:
        start_month = st.text_input("开始月份", "2026.03")
        exam_month = st.text_input("考试月份", "2026.12")
        hours = st.slider("每日可学习时长（小时）", 4, 12, 8)

    if st.button("生成备考计划", type="primary", key="btn_plan"):
        profile = {
            "target": target_school,
            "subjects": subjects,
            "weak": weak,
            "start_month": start_month,
            "exam_month": exam_month,
            "hours": str(hours),
        }
        with st.spinner("正在制定计划..."):
            result = planner.generate_plan(profile)
        st.markdown("---")
        st.markdown(result)


# ===== 功能3：政策问答（仅常见问题快捷按钮，无输入框） =====
with tab3:
    st.header("考研政策智能问答")
    st.write("点击下方常见问题即可获得解答，每条回答均有资料依据，不编造政策条款。")

    # 按类别分组展示所有常见问题
    categories = {}
    for item in POLICIES:
        categories.setdefault(item["category"], []).append(item)

    for cat, items in categories.items():
        st.subheader(cat)
        cols = st.columns(2)
        for i, item in enumerate(items):
            if cols[i % 2].button(item["question"], key=f"qa_{item['id']}", width='stretch'):
                st.session_state["qa_active"] = item["id"]

    if st.session_state.get("qa_active"):
        active_id = st.session_state["qa_active"]
        active = next((p for p in POLICIES if p["id"] == active_id), None)
        if active:
            with st.spinner("正在检索政策资料..."):
                ans, ref = qa.ask(active["question"])
            st.markdown("---")
            st.markdown(f"### {active['question']}")
            st.info(ans)
            st.caption(f"资料依据：{ref}")


# ===== 功能4：院校数据库 =====
with tab4:
    st.header("院校数据库浏览器")
    st.write(f"择校推荐所依据的底层数据，共 {len(_UNIVERSITIES)} 条（示例数据，供演示与算法验证）。")
    col1, col2, col3 = st.columns(3)
    major_filter = col1.selectbox("按专业筛选", ["全部"] + MAJORS, key="db_major")
    region_filter = col2.selectbox("按地区筛选", ["全部"] + REGIONS, key="db_region")
    tier_filter = col3.selectbox("按层次筛选", ["全部", "985", "211", "双一流", "双非"], key="db_tier")

    data = _UNIVERSITIES
    if major_filter != "全部":
        data = [r for r in data if r["专业"] == major_filter]
    if region_filter != "全部":
        data = [r for r in data if r["省份"] == region_filter]
    if tier_filter != "全部":
        data = [r for r in data if r["层次"] == tier_filter]

    st.dataframe(data, width='stretch', hide_index=True)
    st.caption(f"当前显示 {len(data)} 条记录")


st.markdown("---")
st.caption("研途AI · 大语言模型及应用课程项目 | 数据为示例，请以研招网及院校官方招生简章为准")
