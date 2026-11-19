"""RAG 检索引擎：轻量 TF-IDF 实现，零第三方依赖，可离线运行。

设计取舍：
  用 Python 标准库实现字符级 TF-IDF + 余弦相似度，避免依赖 sklearn（体积大、部署慢）。
  流程：语料切分 -> 向量化(TF-IDF) -> 余弦相似度检索 -> 返回 Top-K 片段。
  这是 RAG 中的「检索(Retrieval)」环节；「生成(Generation)」由 llm.py 完成。
"""
import csv
import json
import math
import re
from collections import Counter
import config


def _tokenize_char_ngrams(text: str, n: int = 2) -> list[str]:
    """中文友好的字符 n-gram 切分（去空白与标点）。"""
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。、；：（）()【】\[\]/·,.\-—]", "", text)
    if len(text) < n:
        return [text] if text else []
    return [text[i:i + n] for i in range(len(text) - n + 1)]


class Retriever:
    def __init__(self, documents: list[str], metadatas: list[dict] | None = None):
        self.documents = documents
        self.metadatas = metadatas or [{} for _ in documents]
        self.docs_tokens = [_tokenize_char_ngrams(d) for d in documents]

        # 计算 IDF
        df = Counter()
        for tokens in self.docs_tokens:
            df.update(set(tokens))
        n_docs = max(len(documents), 1)
        self.idf = {t: math.log((n_docs + 1) / (c + 1)) + 1 for t, c in df.items()}

        # 计算每篇文档的 TF-IDF 向量（未归一化此处在检索时归一化）
        self.vectors = [self._vectorize(tokens) for tokens in self.docs_tokens]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        total = max(len(tokens), 1)
        vec = {t: (c / total) * self.idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        q_vec = self._vectorize(_tokenize_char_ngrams(query))
        results = []
        for i, vec in enumerate(self.vectors):
            # 余弦相似度：两向量均已归一化，点积即为相似度
            score = sum(v * vec.get(t, 0.0) for t, v in q_vec.items())
            if score > 0:
                results.append({
                    "score": round(score, 4),
                    "text": self.documents[i],
                    "meta": self.metadatas[i],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def load_policies() -> Retriever:
    """加载政策语料，构造检索器。文档 = 问题 + 答案，便于语义匹配。"""
    with open(config.DATA_DIR / "policies.json", encoding="utf-8") as f:
        items = json.load(f)
    docs = [f"{it['question']}。{it['answer']}" for it in items]
    metas = [{"id": it["id"], "category": it["category"],
              "question": it["question"], "answer": it["answer"]} for it in items]
    return Retriever(docs, metas)


def load_universities() -> list[dict]:
    """用标准库 csv 读取院校库，返回字典列表。"""
    with open(config.DATA_DIR / "universities.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
