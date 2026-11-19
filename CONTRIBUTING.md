# 贡献指南

感谢你对「研途 AI」项目的关注！本项目是大语言模型及应用课程的团队作品，欢迎Issue 反馈与代码贡献。

## 开发环境

```bash
git clone <你的仓库地址>
cd yanlu-ai
python -m venv .venv
# Windows: .venv\Scripts\activate   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python tests/test_smoke.py   # 先跑通冒烟测试
streamlit run app.py         # 启动界面
```

核心逻辑（检索/推荐/计划/问答）全部基于 Python 标准库，只有界面依赖Streamlit。

## 提交流程

1. Fork 仓库并新建分支：`git checkout -b feature/你的功能名`
2. 修改代码后，务必运行冒烟测试：`python tests/test_smoke.py`
3. 提交时写清楚改动：`git commit -m "feat: 新增 XX 功能"`
4. Push 到你的分支并发起 Pull Request。

## 代码约定

- 新增功能请同时补充 `tests/test_smoke.py` 中的测试用例。
- 涉及大模型的逻辑必须保留离线兜底：无 API Key 时功能仍可用。
- 所有院校数据均为示例数据，请在注释和文档中避免将其表述为真实官方数据。
- 不要提交 `.env`、`*.log` 或任何包含真实密钥的文件（已在 `.gitignore` 中排除）。

## 数据更新

院校数据由 `tools/generate_data.py` 生成。若需调整高校池或专业池，请修改脚本中的
`UNIVERSITIES` / `MAJORS` 常量后重新运行：

```bash
python tools/generate_data.py
```

Bug 反馈和功能建议请通过 GitHub Issues 提出，并尽量附上复现步骤。
