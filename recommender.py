"""智能择校模块：结构化检索 + 冲稳保分档 + 大模型解读。

核心思路（体现 RAG 思想）：
  1. 先从本地真实院校库「检索」出符合专业/地区的候选集；
  2. 用录取均分与目标分的差距做「冲/稳/保」分档；
  3. 把候选数据作为上下文交给大模型「生成」解读；离线时用模板兜底。

地区解析（本次修复重点）：
  侧边栏「意向地区」与「其他偏好」文本都可表达地域诉求。
  规则：**其他偏好中识别到的明确地域优先于侧边栏意向地区**，
  因为用户在自由文本里特意写下的地域是更强的个人诉求。
  识别用「数据驱动」方式：省份名/城市名从院校库动态提取，另加常见区域俗称。
  地区无命中时不再静默返回全国数据，而是明确提示，避免地域错配。
"""
from . import llm, rag
from prompts import templates


COLS = ["学校", "省份", "城市", "层次", "专业", "初试科目",
        "复试线", "录取均分", "报录比", "难度"]

# 常见区域俗称 -> 数据中的省份名（用于"其他偏好"文本解析）
REGION_ALIASES = {
    "东北": ["辽宁", "吉林", "黑龙江"],
    "长三角": ["上海", "江苏", "浙江", "安徽"],
    "珠三角": ["广东"],
    "京津冀": ["北京", "天津", "河北"],
    "西南": ["四川", "重庆", "云南", "贵州", "西藏"],
    "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
    "华中": ["湖北", "湖南", "河南"],
    "华南": ["广东", "广西", "海南"],
    "华东": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
    "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
}
# 把这些区域词展开后的省份也纳入词汇表，便于精确匹配
ALL_ALIAS_PROVINCES = {p for ps in REGION_ALIASES.values() for p in ps}

# 明确无地域含义的默认文案，避免误判
_NO_REGION_HINTS = ("不限", "全国", "无偏好", "无所谓", "都可以", "无")


def _region_vocab(df: list[dict]) -> list[str]:
    """从院校库动态提取所有省份名与城市名，按长度降序（优先匹配长词）。"""
    names = set(ALL_ALIAS_PROVINCES)
    for r in df:
        for key in ("省份", "城市"):
            name = (r.get(key) or "").strip()
            if name:
                names.add(name)
    return sorted(names, key=len, reverse=True)


def extract_regions(text: str, df: list[dict]) -> tuple[list[str], str]:
    """从自由文本中识别地域。

    返回 (地区列表, 识别来源说明)。
    具体省/市名优先于区域俗称：文本中若出现明确的省/市名，只取这些；
    否则才把"东北""长三角"等区域俗称展开为省份集合。
    """
    text = (text or "").strip()
    if not text:
        return [], ""

    vocab = _region_vocab(df)

    # 先匹配"XX省/XX市/XX自治区"这类写法：直接按词表匹配即可（"浙江省"含"浙江"）
    specific = [name for name in vocab if name in text]

    # 区域俗称
    areas = [alias for alias in REGION_ALIASES if alias in text]

    if specific:
        # 去掉被更长词包含的结果（如同时命中"吉林"省与"吉林"市，保留即可，去重）
        seen, uniq = set(), []
        for s in specific:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        return uniq, "偏好文本中的明确地区"

    if areas:
        provinces = []
        for alias in areas:
            for p in REGION_ALIASES[alias]:
                if p not in provinces:
                    provinces.append(p)
        return provinces, "偏好文本中的区域（" + "/".join(areas) + "）"

    return [], ""


def resolve_target_regions(profile: dict, df: list[dict]) -> tuple[list[str], str]:
    """确定本次筛选的地区及来源。其他偏好 > 侧边栏意向地区 > 不限。"""
    preference = (profile.get("preference") or "").strip()
    region = (profile.get("region") or "不限").strip()

    # 1) 其他偏好里若写了明确地域，优先采用
    pref_regions, source = extract_regions(preference, df)
    if pref_regions:
        return pref_regions, f"其他偏好（{source}）"

    # 2) 其次用侧边栏意向地区
    if region and region not in _NO_REGION_HINTS:
        # 侧边栏值本身来自数据词表，直接视为一个地区
        return [region], "侧边栏「意向地区」"

    # 3) 不限
    return [], "不限（全国）"


def candidates_to_text(candidates: list[dict]) -> str:
    if not candidates:
        return "（未找到符合条件的院校）"
    lines = ["| " + " | ".join(COLS) + " |"]
    lines.append("|" + "---|" * len(COLS))
    for r in candidates:
        lines.append("| " + " | ".join(str(r.get(c, "")) for c in COLS) + " |")
    return "\n".join(lines)


def _split_tiers(candidates: list[dict], target_score: float) -> dict:
    """按录取均分与目标分的差距分档。"""
    out = {"chong": [], "wen": [], "bao": []}
    for r in candidates:
        try:
            gap = float(r["录取均分"]) - target_score  # 正数=高于目标分
        except (ValueError, KeyError):
            continue
        place = f"{r.get('省份', '')}{r.get('城市', '')}"
        label = f"{r['学校']}（{place}·{r['专业']}，均分{r['录取均分']}）"
        if gap >= 8:
            out["chong"].append(label)
        elif gap >= -6:
            out["wen"].append(label)
        else:
            out["bao"].append(label)
    return out


def recommend(profile: dict) -> str:
    df = rag.load_universities()
    major = (profile.get("major") or "").strip()
    try:
        target = float(profile.get("target_score") or 0)
    except (ValueError, TypeError):
        target = 0.0

    # 1) 确定地区（其他偏好优先）并检索候选集
    target_regions, region_source = resolve_target_regions(profile, df)
    cand = [r for r in df if major in r.get("专业", "")] if major else list(df)
    total_prof = len(cand)

    note = ""
    if target_regions:
        narrowed = [
            r for r in cand
            if any(reg in r.get("省份", "") or reg in r.get("城市", "")
                   for reg in target_regions)
        ]
        if narrowed:
            cand = narrowed
        else:
            # 关键修复：地区无命中时不再静默返回全国数据
            region_txt = "、".join(target_regions)
            note = (
                f"> ⚠️ **地域提醒**：院校库中未找到「{region_txt}」地区开设"
                f"「{major or '该专业'}」的院校记录。下方结果已**放宽为全国范围**，"
                f"地域未能匹配，请留意。\n\n"
            )

    cand.sort(key=lambda r: float(r.get("录取均分", 0) or 0), reverse=True)
    cand_text = candidates_to_text(cand[:12])  # 控制上下文长度

    region_label = "、".join(target_regions) if target_regions else "全国（不限）"

    # 2) 尝试大模型解读；失败/离线则用模板
    llm_profile = dict(profile)
    llm_profile["region"] = region_label
    llm_profile["region_source"] = region_source
    llm_profile["preference"] = (profile.get("preference") or "无").strip() or "无"
    result = llm.recommend(llm_profile, cand_text)
    if result:
        return note + result

    tiers = _split_tiers(cand, target)
    body = templates.MOCK_RECOMMEND_TPL.format(
        major=major or "不限",
        target_score=int(target),
        region=region_label,
        region_source=region_source,
        total_prof=total_prof,
        total_matched=len(cand),
        chong="、".join(tiers["chong"][:4]) or "暂无",
        wen="、".join(tiers["wen"][:4]) or "暂无",
        bao="、".join(tiers["bao"][:4]) or "暂无",
    )
    return note + body
