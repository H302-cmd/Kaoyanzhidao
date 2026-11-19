"""考研政策问答：RAG 检索政策语料 + 大模型生成 + 离线兜底。"""
from . import llm, rag


def ask(question: str) -> tuple[str, str]:
    """返回 (答案文本, 依据资料编号)。"""
    retriever = rag.load_policies()
    hits = retriever.search(question, top_k=3)
    if not hits:
        return "抱歉，资料库中未找到相关政策。建议查阅研招网（yz.chsi.com.cn）官方公告。", "无"

    context = "\n\n".join(
        f"[{h['meta']['id']}]（{h['meta']['category']}）{h['meta']['question']}\n{h['meta']['answer']}"
        for h in hits
    )
    ids = "、".join(h["meta"]["id"] for h in hits)

    answer = llm.answer(question, context)
    if answer:
        return answer, ids

    # 离线模式：直接返回最相关的一条政策（这就是 RAG 检索结果的直接呈现）
    best = hits[0]
    meta = best["meta"]
    text = f"【{meta['category']}】{meta['question']}\n\n{meta['answer']}\n\n（依据资料：{meta['id']}）"
    if len(hits) > 1:
        others = "、".join(h["meta"]["id"] for h in hits[1:])
        text += f"\n\n相关资料：{others}（可在知识库查看）"
    return text, meta["id"]
