# ResearchFlow Backend

FastAPI backend for the ResearchFlow Chat Demo. It keeps the Dify API key on the server side and proxies PDF upload plus chat messages to the Dify Chatflow App.

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=你的Dify应用APIKey
DIFY_USER=researchflow-demo-user
DIFY_TIMEOUT=180
```

## Run

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```powershell
curl http://localhost:8000/api/health
```

Expected:

```json
{ "status": "ok" }
```

## API

### POST `/api/analyze`

Form fields:

- `paper_file`: PDF file
- `research_topic`: research topic
- `extract_metrics`: metrics to extract

Success:

```json
{
  "ok": true,
  "answer": "Dify 返回的 Markdown",
  "conversation_id": "会话 id",
  "raw": {}
}
```

### POST `/api/chat`

JSON body:

```json
{
  "message": "帮我生成研究空白",
  "conversation_id": "上一次返回的 conversation_id"
}
```

## Notes

- The frontend must never call Dify directly.
- The Dify API key must only exist in backend `.env`.
- The implementation uses Dify `/files/upload` and `/chat-messages`, not `/workflows/run`.
- The initial chat payload maps the uploaded file to the Dify start-node file list variable `paper_files`. If your Dify variable name differs, update `build_initial_chat_payload()` in `main.py`.

