"""大模型调用封装：真实 API 模式 + 离线演示模式双通道。

真实模式：调用任意 OpenAI 兼容的 chat/completions 接口。
离线模式：返回 None，由上层模块使用规则引擎/模板生成结果，保证无 Key 也能演示。
"""
import json
import urllib.request
import urllib.error
import config
from prompts import templates


def call(system: str, user: str, temperature: float = 0.6, max_tokens: int = 1400) -> str | None:
    """调用大模型。返回模型文本；离线模式返回 None。"""
    if not config.is_live_mode():
        return None

    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = config.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.LLM_API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # 网络/额度/接口异常时自动降级为离线结果
        print(f"[llm] 调用失败，已降级为离线模式：{exc}")
        return None


def recommend(profile: dict, candidates_text: str) -> str | None:
    user = templates.RECOMMEND_USER.format(
        major=profile.get("major", ""),
        background=profile.get("background", ""),
        target_score=profile.get("target_score", ""),
        region=profile.get("region", ""),
        region_source=profile.get("region_source", "意向地区"),
        preference=profile.get("preference", "无"),
        candidates=candidates_text,
    )
    return call(templates.RECOMMEND_SYSTEM, user)


def plan(profile: dict) -> str | None:
    user = templates.PLAN_USER.format(**profile)
    return call(templates.PLAN_SYSTEM, user)


def answer(question: str, context: str) -> str | None:
    user = templates.QA_USER.format(context=context, question=question)
    return call(templates.QA_SYSTEM, user, temperature=0.3, max_tokens=900)
