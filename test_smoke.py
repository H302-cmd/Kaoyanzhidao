"""冒烟测试：验证核心模块在离线模式下可用（零第三方依赖）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import rag, recommender, planner, qa


def test_data_load():
    uni = rag.load_universities()
    assert len(uni) >= 15000, f"院校数据不足：{len(uni)}"
    assert "学校" in uni[0]
    majors = {r["专业"] for r in uni}
    provinces = {r["省份"] for r in uni}
    schools = {r["学校"] for r in uni}
    assert len(majors) >= 120, f"专业覆盖不足：{len(majors)}"
    assert len(provinces) >= 30, f"地区覆盖不足：{len(provinces)}"
    assert len(schools) >= 500, f"高校覆盖不足：{len(schools)}"
    print(f"[OK] 院校数据：{len(uni)} 条，{len(schools)} 所高校，{len(majors)} 个专业，{len(provinces)} 个省级地区")


def test_top_universities():
    """主流名校与王牌专业覆盖（扩充数据回归测试）。"""
    uni = rag.load_universities()
    schools = {r["学校"] for r in uni}
    must = ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学",
            "南京大学", "中国科学技术大学", "哈尔滨工业大学", "武汉大学",
            "华中科技大学", "中山大学", "同济大学", "厦门大学", "四川大学"]
    missing = [s for s in must if s not in schools]
    assert not missing, f"主流名校缺失：{missing}"
    # 985/211 院校应普遍覆盖计算机专业
    top = {r["学校"] for r in uni if r["层次"] in ("985", "211")}
    with_cs = {r["学校"] for r in uni if r["专业"] == "计算机科学与技术"}
    missing_cs = top - with_cs
    assert not missing_cs, f"主流院校缺少计算机专业：{sorted(missing_cs)[:5]}"
    print("[OK] 主流名校与王牌专业覆盖完整")


def test_region_match():
    """校验院校省份/城市匹配准确（地区错配回归测试）。"""
    uni = rag.load_universities()
    bad = [r for r in uni if r["省份"] == "浙江" and "杭" not in r["城市"]
           and r["城市"] not in ("杭州", "宁波", "温州", "金华", "舟山", "嘉兴", "绍兴", "台州", "丽水", "湖州", "衢州")]
    assert not bad, f"浙江院校城市错配：{[r['学校'] for r in bad][:5]}"
    print("[OK] 院校地区匹配准确")


def test_recommend():
    profile = {
        "major": "计算机科学与技术", "background": "双非本科", "target_score": 350,
        "region": "不限", "preference": "无",
    }
    result = recommender.recommend(profile)
    assert "冲一冲" in result and "保底" in result
    print("[OK] 择校推荐生成成功（含冲/稳/保三档）")


def test_preference_region():
    """其他偏好里的地域优先于侧边栏，且结果院校地域一致（本次修复回归）。"""
    uni = rag.load_universities()
    # 1) 偏好写地域时优先识别
    p = {"major": "计算机科学与技术", "region": "不限",
         "preference": "想去杭州发展", "target_score": 350}
    regions, source = recommender.resolve_target_regions(p, uni)
    assert regions == ["杭州"], f"偏好地域识别错误：{regions}"
    assert "其他偏好" in source

    # 2) 偏好与侧边栏冲突时以偏好为准
    p2 = {"major": "计算机科学与技术", "region": "浙江",
          "preference": "想去江苏", "target_score": 350}
    regions2, _ = recommender.resolve_target_regions(p2, uni)
    assert regions2 == ["江苏"], f"偏好未优先：{regions2}"

    # 3) 默认偏好时回退到侧边栏地区
    p3 = {"major": "计算机科学与技术", "region": "浙江",
          "preference": "想留在意向地区发展", "target_score": 350}
    regions3, source3 = recommender.resolve_target_regions(p3, uni)
    assert regions3 == ["浙江"] and "侧边栏" in source3

    # 4) 区域俗称展开
    p4 = {"major": "计算机科学与技术", "region": "不限",
          "preference": "长三角都可以", "target_score": 350}
    regions4, _ = recommender.resolve_target_regions(p4, uni)
    assert set(regions4) == {"上海", "江苏", "浙江", "安徽"}, regions4

    # 5) 结果中的院校地域全部一致（不串地区）
    out = recommender.recommend(p)
    recommended = [ln for ln in out.split("\n") if ln.startswith("【")]
    assert recommended, "未生成分档结果"
    tiers_text = "\n".join(recommended)
    assert "杭州" in tiers_text, f"结果未落在偏好地区杭州：{tiers_text[:120]}"
    print("[OK] 其他偏好地域识别/优先级/区域展开/结果地域一致性 全部通过")


def test_region_no_match_warning():
    """地区无对应专业时给出明确警告，而非静默返回全国数据。"""
    uni = rag.load_universities()
    # 找一个该地区确实没有的专业组合
    pair = None
    for prov in sorted({r["省份"] for r in uni}):
        for maj in sorted({r["专业"] for r in uni}):
            if not any(r["省份"] == prov and r["专业"] == maj for r in uni):
                pair = (prov, maj)
                break
        if pair:
            break
    assert pair, "未找到可用于测试的无数据组合"
    prov, maj = pair
    out = recommender.recommend({"major": maj, "region": "不限",
                                 "preference": f"想去{prov}", "target_score": 350})
    assert "地域提醒" in out, "地区无命中时未给出警告"
    print(f"[OK] 地区无命中警告正常（{prov}无{maj}）")


def test_plan():
    profile = {
        "target": "浙江大学 计算机", "subjects": "政治/英语一/数学一/数据结构",
        "start_month": "2026.03", "exam_month": "2026.12",
        "hours": "9", "weak": "数学",
    }
    result = planner.generate_plan(profile)
    for section in ["总体策略", "三阶段规划", "月度任务拆解", "一周时间分配表", "自检清单", "避坑指南"]:
        assert section in result, f"计划缺少章节：{section}"
    assert "| 上午" in result, "计划缺少一周时间表"
    print("[OK] 备考计划生成成功（六大章节齐全，含时间表）")


def test_qa():
    ans, ref = qa.ask("调剂系统可以填报几个志愿？")
    assert len(ans) > 20 and ref != "无"
    print(f"[OK] 政策问答成功（依据 {ref}）")


def test_policy_count():
    import json
    import config
    with open(config.DATA_DIR / "policies.json", encoding="utf-8") as f:
        items = json.load(f)
    assert len(items) >= 35, f"政策条目不足：{len(items)}"
    print(f"[OK] 政策语料：{len(items)} 条")


if __name__ == "__main__":
    test_data_load()
    test_top_universities()
    test_region_match()
    test_recommend()
    test_preference_region()
    test_region_no_match_warning()
    test_plan()
    test_qa()
    test_policy_count()
    print("\n全部冒烟测试通过！")
