# GitHub 推送与部署指南

本仓库已完成本地 Git 初始化并生成首次提交。按下面步骤即可推到 GitHub 并获得可访问的网站网址。

---

## 一、推送到 GitHub

### 1. 在 GitHub 上新建一个空仓库

1. 打开 <https://github.com/new>
2. Repository name 建议填 `yanlu-ai`（或你喜欢的名字）
3. **不要**勾选 "Add a README file"、".gitignore"、"License"——保持仓库完全为空
4. 点击 Create repository

### 2. 本地关联远程仓库并推送

在项目目录 `yanlu-ai` 下执行（把 `你的用户名` 和 `仓库名` 换成实际的）：

```bash
# 关联远程仓库
git remote add origin https://github.com/你的用户名/仓库名.git

# 确认分支名为 main
git branch -M main

# 推送（-u 表示以后可直接 git push）
git push -u origin main
```

> 💡 若推送时要求登录：GitHub 已不再支持用账号密码推送，需要使用 **Personal Access Token (PAT)**。
> 生成方式：GitHub 头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，
> 勾选 `repo` 权限，把生成的 token 当作密码粘贴即可。

### 3. 验证推送成功

刷新 GitHub 仓库页面，应能看到全部文件。检查：

- ✅ `README.md` 正常渲染（徽章、表格、架构图）
- ✅ 没有 `.env`、`.wb_pipeline/` 等敏感或内部文件
- ✅ `data/` 下有 `universities.csv` 和 `policies.json`

---

## 二、部署到公网（获得网站网址）

### 方案 A：Streamlit Community Cloud（推荐，免费）

1. 打开 <https://share.streamlit.io>，用 GitHub 账号登录并授权
2. 点击 **New app**，填写：
   - Repository：选择刚推送的仓库
   - Branch：`main`
   - Main file path：`app.py`
3. （可选）点 **Advanced settings** → Secrets，填入：

   ```toml
   LLM_API_KEY = "你的真实密钥"
   LLM_PROVIDER = "deepseek"
   LLM_BASE_URL = "https://api.deepseek.com/v1"
   LLM_MODEL = "deepseek-chat"
   ```

   不填也能以离线演示模式正常运行。

4. 点击 **Deploy**，等待 1-2 分钟，得到形如 `https://xxx.streamlit.app` 的网址。
5. 把这个网址回填到 `README.md` 顶部的「在线演示」处，再 `git push` 一次。

### 方案 B：Hugging Face Spaces

1. 打开 <https://huggingface.co/new-space>，SDK 选择 **Streamlit**
2. 把本仓库文件全部上传到该 Space
3. 在 Space 的 Settings → Repository secrets 中配置 `LLM_API_KEY`
4. 片刻后即可获得公开网址。

---

## 三、推送后回填清单

部署完成后，请回填以下三处占位内容：

| 位置 | 占位符 | 替换为 |
|---|---|---|
| `README.md` 徽章与链接 | `OWNER/REPO` | 你的 GitHub 用户名 / 仓库名 |
| `README.md` 在线演示 | `#` / 部署说明 | 实际部署网址 |
| `README.md` 团队分工 | `成员 A/B/C` | 真实姓名与分工 |

---

## 四、常用 Git 命令速查

```bash
git status                 # 查看当前改动
git add .                  # 暂存所有改动（.gitignore 中的文件会被忽略）
git commit -m "说明"       # 提交
git push                   # 推送到远程（首次推送后）
git pull                   # 拉取远程更新
```

---

## 五、安全提醒

- `LLM_API_KEY` 等真实密钥**只能**放在本地 `.env` 或云端 Secrets 中，**绝不**提交到仓库。
- `.gitignore` 已排除 `.env`、`.streamlit/secrets.toml`、日志等敏感文件。
- 提交前可用 `git status` 检查待提交文件清单，确认无敏感信息。
