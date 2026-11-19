"""全局配置：读取 .env，决定真实大模型模式 / 离线演示模式。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPTS_DIR = BASE_DIR / "prompts"

# 大模型配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
# 兼容用户只填域名、未带 /v1 的情况
if LLM_BASE_URL and not LLM_BASE_URL.rstrip("/").endswith("/v1"):
    LLM_BASE_URL = LLM_BASE_URL.rstrip("/") + "/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")


def is_live_mode() -> bool:
    """是否运行在真实大模型模式。

    仅当 Key 看起来是真实密钥时才启用：
      - 以 sk- 开头
      - 不含非 ASCII 字符（占位符常写成 sk-您复制的密钥 / sk-xxx）
      - 长度足够（真实 Key 通常远超 20 位）
    否则一律走离线演示模式，保证占位符不会误触发网络请求。
    """
    key = (LLM_API_KEY or "").strip()
    if not key.startswith("sk-"):
        return False
    try:
        key.encode("ascii")
    except UnicodeEncodeError:
        return False
    return len(key) >= 20


MODE_LABEL = "真实大模型模式" if is_live_mode() else "离线演示模式"
