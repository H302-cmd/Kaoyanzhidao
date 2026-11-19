"""备考计划生成模块：大模型 Agent 生成 + 离线规则引擎兜底。

离线引擎会根据用户填写的目标、科目、时长、薄弱项，动态拼装出
一份包含总体策略、三阶段规划、月度任务、一周时间表、自检清单和
避坑指南的详细计划，而非静态模板。
"""
from datetime import datetime
from . import llm


def _month_add(month_str: str, delta: int) -> str:
    """'2026.03' 加 delta 个月后返回 'YYYY.MM' 字符串。"""
    try:
        y, m = month_str.replace("-", ".").split(".")[:2]
        total = int(y) * 12 + int(m) - 1 + delta
        return f"{total // 12}.{total % 12 + 1:02d}"
    except Exception:
        return month_str


def _month_span(start: str, end: str) -> int:
    try:
        s = datetime.strptime(start.replace("-", ".") + "-01", "%Y-%m-%d")
        e = datetime.strptime(end.replace("-", ".") + "-01", "%Y-%m-%d")
        return max((e.year - s.year) * 12 + (e.month - s.month), 1)
    except Exception:
        return 9


def _detect_subjects(text: str) -> list[str]:
    """从科目字符串中识别涉及的科目类型。"""
    text = text or ""
    keywords = {
        "政治": ["政治", "思修", "马原", "毛中特"],
        "英语": ["英语", "英一", "英二", "外语"],
        "数学": ["数学", "高数", "数一", "数二", "数三", "线代", "概率"],
        "专业课": ["专业", "专业课", "综合", "数据结构", "法学", "教育学", "心理学", "金融学", "会计"],
    }
    found = []
    for name, kws in keywords.items():
        if any(k in text for k in kws):
            found.append(name)
    return found or ["政治", "英语", "数学", "专业课"]


# 各科在三阶段的针对性任务（离线引擎素材库）
SUBJECT_TASKS = {
    "政治": {
        "基础": "通读教材，重点是马原原理和毛中特框架，每天 30 分钟即可，不必背诵",
        "强化": "刷选择题真题（肖秀荣/徐涛 1000 题），建立错题本，开始梳理时政",
        "冲刺": "背诵肖四肖八主观题，每天一套选择题保持手感，限时模拟",
    },
    "英语": {
        "基础": "每天背 100 个单词（用墨墨/不背单词），精读真题阅读长难句",
        "强化": "真题阅读二刷，总结错题题型，开始整理作文模板和万能句型",
        "冲刺": "整套真题限时模拟，作文模板默写熟练，保持每两天一篇阅读",
    },
    "数学": {
        "基础": "过一遍教材与基础课，整理公式定理卡片，完成课后基础习题",
        "强化": "刷强化习题集（如 660/880），按题型归纳方法，重点攻克薄弱章节",
        "冲刺": "近 15 年真题按套卷限时做，查漏补缺，回归错题本",
    },
    "专业课": {
        "基础": "通读指定参考书，搭建知识框架图，整理笔记",
        "强化": "研究历年真题，归纳高频考点，开始背诵核心概念",
        "冲刺": "真题三刷 + 模拟题，完善论述题答题框架，查漏补缺",
    },
}

WEAK_TIPS = {
    "数学": "数学是拉分大户，建议每天上午头脑清醒时安排 2-3 小时，务必动手算而非只看视频；错题要隔周重做。",
    "英语": "英语贵在坚持，单词要天天背不能断；阅读错题要分析是定位问题还是理解问题，别只对了答案就翻篇。",
    "政治": "政治性价比在后期，8 月前不必投入过多；主观题一定要动手写、对照答案找差距，别只背书。",
    "专业课": "专业课分数占比高，务必以目标院校指定书目和真题为准，尽早联系上岸学长学姐获取一手资料。",
}

WEEK_TABLE = """| 时间段 | 周一 | 周二 | 周三 | 周四 | 周五 | 周六 | 周日 |
|---|---|---|---|---|---|---|---|
| 上午（2-3h） | {math} | {math} | {math} | {math} | {math} | {math} | {math} |
| 下午（2-3h） | {major} | {major} | {major} | {major} | {major} | {major} | {major} |
| 晚上（2h） | {english} | {politics} | {english} | {politics} | {english} | {review} | {review} |"""


def _subject_hours(hours: float) -> dict:
    """按每日总时长分配各科时长（字符串描述）。"""
    if hours >= 9:
        return {"math": "数学 3h", "major": "专业课 3h", "english": "英语 2h",
                "politics": "政治 1h", "review": "本周复盘"}
    if hours >= 7:
        return {"math": "数学 2.5h", "major": "专业课 2.5h", "english": "英语 1.5h",
                "politics": "政治 0.5h", "review": "本周复盘"}
    return {"math": "数学 2h", "major": "专业课 2h", "english": "英语 1.5h",
            "politics": "政治 0.5h", "review": "本周复盘"}


def _build_detailed_plan(profile: dict) -> str:
    target = profile.get("target") or "目标院校"
    subjects_text = profile.get("subjects") or ""
    weak = (profile.get("weak") or "无").strip() or "无"
    start = profile.get("start_month") or "2026.03"
    exam = profile.get("exam_month") or "2026.12"
    try:
        hours = float(profile.get("hours") or 8)
    except (ValueError, TypeError):
        hours = 8.0

    subjects = _detect_subjects(subjects_text)
    total_months = _month_span(start, exam)
    base_end = _month_add(start, round(total_months * 0.44))
    strong_start = _month_add(start, round(total_months * 0.44) + 1)
    strong_end = _month_add(start, round(total_months * 0.78))
    sprint_start = _month_add(start, round(total_months * 0.78) + 1)

    lines = []
    lines.append(f"# {target} 备考全周期计划")
    lines.append("")
    lines.append(f"> 备考周期：{start} — {exam}（约 {total_months} 个月 / {total_months * 4} 周）｜"
                 f"每日投入：约 {hours:g} 小时｜初试科目：{subjects_text or '未填写'}")
    lines.append("")

    # 1 总体策略
    lines.append("## 一、总体策略")
    lines.append("")
    lines.append(f"以「{('、'.join(subjects))}」为复习主线，"
                 f"基础阶段重理解、强化阶段重刷题、冲刺阶段重模拟。"
                 f"{('其中「' + weak + '」为当前薄弱项，需要从基础阶段起持续投入额外时间。') if weak != '无' else '各科均衡推进，注意定期自检。'}")
    lines.append("")

    # 2 三阶段规划
    lines.append("## 二、三阶段规划")
    lines.append("")
    stages = [
        ("基础阶段", start, base_end, "建立完整知识框架，弄懂每一个知识点", "基础"),
        ("强化阶段", strong_start, strong_end, "由点及面，刷题归纳，形成解题体系", "强化"),
        ("冲刺阶段", sprint_start, exam, "全真模拟，查漏补缺，稳定应试状态", "冲刺"),
    ]
    for name, s, e, goal, key in stages:
        lines.append(f"### {name}（{s} — {e}）")
        lines.append("")
        lines.append(f"**阶段目标**：{goal}")
        lines.append("")
        for sub in subjects:
            task = SUBJECT_TASKS.get(sub, {}).get(key, "按参考书系统复习")
            lines.append(f"- **{sub}**：{task}")
        lines.append("")

    # 3 月度任务拆解
    lines.append("## 三、月度任务拆解")
    lines.append("")
    lines.append("| 月份 | 阶段 | 本月重点任务 |")
    lines.append("|---|---|---|")
    month_focus = {
        "基础": "通读教材 + 建立框架 + 打牢基础题",
        "强化": "真题专项 + 题型归纳 + 核心考点背诵",
        "冲刺": "整套模拟 + 错题回归 + 主观题模板",
    }
    for i in range(total_months):
        m = _month_add(start, i)
        if i <= round(total_months * 0.44):
            stage, focus = "基础", month_focus["基础"]
        elif i <= round(total_months * 0.78):
            stage, focus = "强化", month_focus["强化"]
        else:
            stage, focus = "冲刺", month_focus["冲刺"]
        extra = f"；重点补「{weak}」" if weak != "无" and i % 2 == 0 else ""
        lines.append(f"| {m} | {stage} | {focus}{extra} |")
    lines.append("")

    # 4 一周时间表
    lines.append("## 四、一周时间分配表")
    lines.append("")
    lines.append("> 下表为强化阶段的典型安排，可按各科进度微调；基础阶段减少刷题、冲刺阶段增加模拟。")
    lines.append("")
    h = _subject_hours(hours)
    lines.append(WEEK_TABLE.format(**h))
    lines.append("")

    # 5 自检清单
    lines.append("## 五、每月自检清单")
    lines.append("")
    checks = [
        f"{subjects[0] if subjects else '核心科目'}本月计划的任务是否全部完成？",
        "错题本是否每周更新，且去重后重做过一遍？",
        f"薄弱科目「{weak}」的投入时间是否达到计划？" if weak != "无" else "各科时间分配是否均衡？",
        "英语单词是否做到每天打卡、没有中断？",
        "本月是否至少完成一次限时模拟或自测？",
        "知识框架图是否随复习进度持续补充完善？",
        "下月目标是否明确、可量化？",
    ]
    for c in checks:
        lines.append(f"- [ ] {c}")
    lines.append("")

    # 6 避坑指南
    lines.append("## 六、避坑指南与结语")
    lines.append("")
    tips = [WEAK_TIPS.get(weak, WEAK_TIPS["专业课"])]
    tips.append("避免只收藏资料不执行：计划的价值在于每天落实，建议每晚花 5 分钟勾选当日完成项。")
    tips.append("警惕假努力：用学习时长衡量不如用「完成任务数 + 正确率」衡量，定期用真题检验真实水平。")
    for t in tips:
        lines.append(f"- {t}")
    lines.append("")
    lines.append(f"备考是一场马拉松，{target} 的目标完全可实现。"
                 "把大目标拆成每天的小任务，坚持到最后，时间会给你答案。加油！")
    lines.append("")
    lines.append("---")
    lines.append("*提示：当前为离线演示模式，计划由规则引擎根据你填写的信息动态生成。*")

    return "\n".join(lines)


def generate_plan(profile: dict) -> str:
    """优先调用大模型；失败或离线时用规则引擎生成详细计划。"""
    result = llm.plan(profile)
    if result:
        return result
    return _build_detailed_plan(profile)
