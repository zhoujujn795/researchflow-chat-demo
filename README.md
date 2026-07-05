# 科研文献数据化分析智能体 Demo

这是一个“科研文献数据化分析智能体”的前后端 Demo。它对接你已经在 Dify 中搭建好的 Chatflow App：

论文 PDF → MinerU 解析论文 → 参数提取 → 结构化数据整理 → LLM 生成科研分析报告

本项目只负责前端页面和后端接口，不重新实现 MinerU、参数提取器或大模型逻辑。

## 技术栈

前端：

- Vue 3
- Vite
- marked
- DOMPurify
- lucide-vue-next

后端：

- FastAPI
- requests
- python-dotenv
- python-multipart

## 项目结构

```text
researchflow-chat-demo/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── README.md
│   └── tests/
│       └── test_main_helpers.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api.js
│       └── style.css
└── README.md
```

## 配置 Dify API Key

复制后端环境变量模板：

```powershell
cd backend
copy .env.example .env
```

编辑 `backend/.env`：

```env
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=你的Dify应用APIKey
DIFY_USER=researchflow-demo-user
DIFY_TIMEOUT=180
```

注意：

- `DIFY_API_KEY` 只能放在后端 `.env`。
- 前端不能直接调用 Dify。
- 后端通过 `Authorization: Bearer {DIFY_API_KEY}` 调用 Dify。

## 启动后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端默认地址：

```text
http://localhost:8000
```

健康检查：

```powershell
curl http://localhost:8000/api/health
```

## 启动前端

```powershell
cd frontend
npm install
npm run dev
```

如果 PowerShell 禁止执行 `npm.ps1`，可以改用：

```powershell
npm.cmd install
npm.cmd run dev
```

前端默认访问：

```text
http://localhost:5173
```

## 如何测试上传 PDF

1. 启动后端并确认 `.env` 中的 `DIFY_API_KEY` 有效。
2. 启动前端，打开 `http://localhost:5173`。
3. 上传一篇 PDF 科研论文。
4. 填写研究主题，例如：

```text
城市空气质量 PM2.5 变化趋势与影响因素分析
```

5. 填写希望提取的指标，例如：

```text
PM2.5、PM10、R²、MAE、RMSE、Pearson 相关系数、特征重要性
```

6. 点击“开始分析”。
7. 等待 Dify 返回 Markdown 报告。
8. 使用底部追问框继续提问，例如：

```text
帮我生成研究空白
```

## 后端接口

### `POST /api/analyze`

第一次上传论文并开始分析。

请求类型：`multipart/form-data`

字段：

- `paper_file`: PDF 文件
- `research_topic`: 研究主题
- `extract_metrics`: 希望提取的指标

### `POST /api/chat`

继续追问。

```json
{
  "message": "帮我提取 R²、MAE、RMSE",
  "conversation_id": "上一次返回的 conversation_id"
}
```

### `GET /api/health`

```json
{
  "status": "ok"
}
```

## 常见问题

### 401：API Key 错误

检查 `backend/.env` 中的 `DIFY_API_KEY` 是否来自对应的 Dify 对话型应用。修改后重启后端。

### 504：Dify 或模型超时

论文较长、模型排队或工作流耗时较长时可能出现。可以调大 `DIFY_TIMEOUT`，或先用较短 PDF 测试。

### 文件上传失败

确认上传的是 PDF 文件，并检查 Dify 应用是否支持文件输入。后端当前使用 `/files/upload` 后将 `upload_file_id` 放入 `/chat-messages` 的 `files` 数组。

### conversation_id 丢失

前端会把 `conversation_id` 存入 `localStorage`。点击“清空会话”会删除它；更换浏览器或清理站点数据也会导致丢失。

### Dify 文件变量不是 files 数组

如果你的 Dify 开始节点定义了 `paper_file` 文件变量，请查看 `backend/main.py` 中 `build_initial_chat_payload()` 的注释，把文件对象切换到 `inputs.paper_file` 模式。

## 后续扩展方向

- 多篇论文批量上传
- 文献指标矩阵
- 研究空白分析
- Supabase 入库
- CSV / Excel 导出
- 论文分析历史记录
- 多用户登录和配额控制
## 部署到 Vercel

本项目已经按单个 Vercel FastAPI 应用配置：Vercel 运行 `backend.main:app`，构建时会执行 `cd frontend && npm install && npm run build`，后端会在生产环境托管 `frontend/dist`。

### 需要提交的部署文件

- `pyproject.toml`：声明 Python 运行时依赖、Python 版本和 Vercel FastAPI 入口。
- `vercel.json`：配置 `backend/main.py` 这个函数的最大运行时长为 300 秒，并排除测试、源码和缓存文件。
- `backend/main.py`：生产环境存在 `frontend/dist` 时会返回前端静态页面。
- `frontend/src/api.js`：生产环境同域请求 `/api`，本地开发仍请求 `http://localhost:8000`。

### Vercel 环境变量

在 Vercel Project Settings → Environment Variables 中配置：

```env
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=你的Dify应用APIKey
DIFY_USER=researchflow-demo-user
DIFY_TIMEOUT=180
```

不要配置 `VITE_API_BASE_URL`，除非你把后端部署到另一个域名。默认同域部署时前端会直接请求 `/api/analyze` 和 `/api/chat`。

### 通过 Git 部署

1. 把 `researchflow-chat-demo/` 作为项目根目录提交到 GitHub、GitLab 或 Bitbucket。
2. 在 Vercel 新建项目并选择该仓库。
3. 如果仓库根目录不是 `researchflow-chat-demo/`，在 Vercel 的 Root Directory 选择 `researchflow-chat-demo`。
4. 保持 Build Command 为空或使用项目文件中的默认配置。
5. 配好上面的环境变量后部署。
6. 部署完成后访问 `https://你的项目域名/api/health`，应返回 `{ "status": "ok" }`。

### 通过 Vercel CLI 部署

```powershell
cd researchflow-chat-demo
npm install -g vercel
vercel login
vercel
vercel env add DIFY_API_KEY production
vercel env add DIFY_BASE_URL production
vercel env add DIFY_USER production
vercel env add DIFY_TIMEOUT production
vercel --prod
```

如果论文分析经常超过 300 秒，当前阻塞式接口会被 Vercel 终止；那时需要改成异步任务、流式返回或把后端部署到更适合长任务的平台。

