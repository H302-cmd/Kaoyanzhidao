<div align="center">

# 🎓 研途 AI · 考研全周期智能规划助手

**用「真实数据检索 + 大模型生成」，陪一个考研生走完从择校到调剂的全过程。**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/OWNER/REPO?style=social)](https://github.com/OWNER/REPO/stargazers)

> 大语言模型及应用课程 · 团队合作项目

</div>

---

## 🔗 在线演示

> 🚀 **在线体验**：[点击访问部署网址](#)　（部署后可把 `#` 替换为 Streamlit Cloud 地址，如 `https://yanlu-ai.streamlit.app`）
>
> 💻 尚未部署？[本地运行](#-快速开始) 只需 3 步，不配置 API Key 也能体验全部功能。

---

## ✨ 项目简介

考研信息高度不对称：**择校靠猜、备考计划靠抄、政策靠道听途说**。信息散落在研招网、各校招生简章和经验帖中，考生很难在短时间内做出科学决策。

**研途 AI** 把分散的院校招生数据整理成结构化知识库，用 RAG（检索增强生成）技术**先检索真实数据、再由大语言模型生成个性化解读**，覆盖「择校 → 备考计划 → 政策问答 → 调剂参考」的完整链路。

**三个核心特点：**

| | 说明 |
|---|---|
| 🛡️ **数据可信** | 所有具体数字来自本地院校库，模型只做解读、不编造数据，从机制上抑制幻觉 |
| 🔀 **双模式运行** | 配了 API Key 走真实大模型；不配则自动进入离线演示模式，功能照常可用——任何网络环境都能演示 |
| ⚡ **零依赖核心** | 检索与推荐逻辑用 Python 标准库实现，部署轻量、启动飞快 |

---

## 🎯 功能一览

| 功能 | 说明 | 关键技术 |
|---|---|---|
| 🎯 **智能择校** | 覆盖 **147 个专业 × 526 所高校 × 31 个省级地区**，按分数自动分「冲/稳/保」三档；支持从「其他偏好」文本识别地域（省/市/区域俗称），确保结果地域一致 | 结构化检索 + 地域解析 + 分档算法 + LLM 解读 |
| 📅 **备考计划** | 按目标、科目、每日时长生成含三阶段规划、月度任务拆解、一周时间表、自检清单、避坑指南的详细计划 | LLM Agent + 动态规则引擎兜底 |
| 📚 **政策问答** | **40 个常见问题**一键查询，按 **11 个类别**分组，每条回答标注资料编号，有据可查 | RAG（TF-IDF 检索）+ LLM 生成 |
| 🏫 **院校数据库** | **19888 条**示例数据，覆盖全部 985/211/双一流及各省重点本科，支持专业/地区/层次三维筛选 | CSV 结构化数据 |

### 界面预览

> 📷 部署后在此处放 2-3 张界面截图，例如：
>
> | 智能择校 | 备考计划 | 政策问答 |
> |---|---|---|
> | ![择校](docs/screenshots/择校.png) | ![计划](docs/screenshots/计划.png) | ![问答](docs/screenshots/问答.png) |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────┐
│  交互层    Streamlit Web 界面（4 个模块）   │
├─────────────────────────────────────────┤
│  应用层    择校推荐 / 计划生成 / 政策问答     │
├─────────────────────────────────────────┤
│  AI 层     LLM 封装(双模式) + RAG 检索引擎   │
├─────────────────────────────────────────┤
│  数据层    院校库 CSV + 政策语料 JSON        │
└─────────────────────────────────────────┘
```

**RAG 流程**：`语料切分 → 字符级 TF-IDF 向量化 → 余弦相似度检索 → 拼接上下文 → 大模型生成`。
未配置 Key 或调用失败时自动降级为规则引擎/模板输出，服务不中断。

**技术栈**：`Python` · `Streamlit` · `TF-IDF / 余弦相似度` · `OpenAI 兼容 API（DeepSeek / 通义千问等）` · `CSV / JSON`

---

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/OWNER/REPO.git
cd REPO

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3.（可选）配置真实大模型：复制示例文件并填入 API Key
cp .env.example .env        # Windows 用 copy .env.example .env
# 编辑 .env，填入 LLM_API_KEY；不填也能以离线演示模式运行

# 4. 启动应用
streamlit run app.py
```

浏览器打开终端提示的地址（默认 <http://localhost:8501>）即可使用。

### 核心模块自检（无需 Streamlit）

```bash
python tests/test_smoke.py
```

通过即表示数据加载、择校推荐、备考计划、政策问答等逻辑正常。

---

## ☁️ 部署到公网

推荐 **Streamlit Community Cloud**（免费），3 分钟拿到公开网址：

1. 把本项目推送到你的 GitHub 仓库（见 [PUSH_GUIDE.md](PUSH_GUIDE.md)）；
2. 登录 [share.streamlit.io](https://share.streamlit.io)，选择该仓库与 `app.py`；
3. 在 Advanced Settings 里配置 Secrets（`LLM_API_KEY` 等，不填也能以演示模式运行）；
4. 点击 Deploy，得到形如 `https://xxx.streamlit.app` 的网址，回填到本页顶部。

也可部署到 Hugging Face Spaces（Space SDK 选 Streamlit），步骤类似。

---

## 📁 目录结构

```
yanlu-ai/
├── app.py                    # Streamlit 主界面
├── config.py                 # 配置与运行模式判断
├── requirements.txt          # 依赖清单
├── .env.example              # 环境变量示例
├── LICENSE                   # MIT 开源许可
├── CONTRIBUTING.md           # 贡献指南
├── PUSH_GUIDE.md             # GitHub 推送与部署指南
├── data/
│   ├── universities.csv      # 院校示例数据（19888 条，526 所高校 × 147 个专业）
│   └── policies.json         # 考研政策语料（40 条，11 个类别）
├── prompts/
│   └── templates.py          # Prompt 模板库
├── src/
│   ├── llm.py                # 大模型调用封装（双模式）
│   ├── rag.py                # RAG 检索引擎（纯标准库 TF-IDF）
│   ├── recommender.py        # 智能择校
│   ├── planner.py            # 备考计划生成
│   └── qa.py                 # 政策问答
├── tools/
│   └── generate_data.py      # 院校数据生成器（可复现）
├── tests/
│   └── test_smoke.py         # 冒烟测试
└── docs/
    ├── 项目报告.docx          # 课程作业报告
    ├── 路演稿.md             # 课堂路演讲稿
    └── screenshots/          # 界面截图（部署后补充）
```

---

## ⚠️ 数据说明

项目内的院校分数线、报录比、招生人数等均为**用于算法演示的示例数据**，不构成报考建议。
正式报考请以中国研究生招生信息网（yz.chsi.com.cn）及各院校最新招生简章为准。

---

## 👥 团队分工

> 请按团队实际情况修改下表，并补充各成员具体完成的工作。

| 成员 | 分工 |
|---|---|
| 成员 A | 数据与 RAG 检索引擎（院校库整理、TF-IDF 检索） |
| 成员 B | 大模型应用（LLM 封装、择校/计划/问答 Prompt 与 Agent 逻辑） |
| 成员 C | 前端界面、部署、文档与路演准备 |

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

<div align="center">

Made with ❤️ for 考研人 · 大语言模型及应用课程项目

**如果这个项目对你有帮助，欢迎点一个 ⭐ Star！**

</div>
