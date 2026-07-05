import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from requests import Response

load_dotenv()

DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_USER = os.getenv("DIFY_USER", "researchflow-demo-user")
DIFY_TIMEOUT = float(os.getenv("DIFY_TIMEOUT", "180"))


class DifyResponseError(Exception):
    """Raised when Dify returns a syntactically valid but unusable response."""


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = ""


app = FastAPI(title="ResearchFlow Chat Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ok_response(answer: str, conversation_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "answer": answer,
        "conversation_id": conversation_id,
        "raw": raw,
    }


def error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"ok": False, "message": message})


def validate_pdf_upload(filename: str | None, content_type: str | None) -> str | None:
    if not filename:
        return "请先上传 PDF 文件。"

    if not filename.lower().endswith(".pdf"):
        return "只支持上传 PDF 文件。"

    if content_type and content_type not in {"application/pdf", "application/octet-stream"}:
        return "只支持上传 PDF 文件。"

    return None


def require_dify_api_key() -> str | None:
    if not DIFY_API_KEY:
        return "后端未配置 DIFY_API_KEY，请先在 backend/.env 中配置。"
    return None


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {DIFY_API_KEY}"}


def extract_dify_error_message(response: Response, prefix: str) -> str:
    detail = ""
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = str(
                payload.get("message")
                or payload.get("error")
                or payload.get("detail")
                or payload
            )
    except ValueError:
        detail = response.text.strip()

    if not detail:
        detail = f"HTTP {response.status_code}"

    return f"{prefix}：{detail}"


def extract_chat_answer(payload: dict[str, Any]) -> tuple[str, str]:
    answer = payload.get("answer")
    if not answer:
        raise DifyResponseError("Dify 返回结果中没有 answer。")

    conversation_id = payload.get("conversation_id") or ""
    return str(answer), str(conversation_id)


def upload_file_to_dify(paper_file: UploadFile) -> str:
    paper_file.file.seek(0)
    response = requests.post(
        f"{DIFY_BASE_URL}/files/upload",
        headers=auth_headers(),
        data={"user": DIFY_USER},
        files={
            "file": (
                paper_file.filename,
                paper_file.file,
                paper_file.content_type or "application/pdf",
            )
        },
        timeout=DIFY_TIMEOUT,
    )

    if response.status_code >= 400:
        if response.status_code == 504:
            raise DifyResponseError("Dify 文件上传超时，请稍后重试。")
        raise DifyResponseError(extract_dify_error_message(response, "Dify 文件上传失败"))

    payload = response.json()
    upload_file_id = payload.get("id")
    if not upload_file_id:
        raise DifyResponseError("Dify 文件上传成功但没有返回文件 id。")

    return str(upload_file_id)


def call_dify_chat(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{DIFY_BASE_URL}/chat-messages",
        headers={**auth_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=DIFY_TIMEOUT,
    )

    if response.status_code >= 400:
        if response.status_code == 504:
            raise DifyResponseError("Dify 对话接口超时，请稍后重试或降低论文长度。")
        raise DifyResponseError(extract_dify_error_message(response, "Dify 对话接口调用失败"))

    return response.json()


def build_initial_chat_payload(
    upload_file_id: str,
    research_topic: str,
    extract_metrics: str,
) -> dict[str, Any]:
    return {
        "inputs": {
            "research_topic": research_topic,
            "extract_metrics": extract_metrics,
            # If your Dify start node defines a file variable named paper_file
            # instead of receiving files from the top-level files array, switch to:
            # "paper_file": {
            #     "type": "document",
            #     "transfer_method": "local_file",
            #     "upload_file_id": upload_file_id,
            # }
        },
        "query": "请分析我上传的科研论文 PDF，提取结构化指标，并生成科研分析报告。",
        "response_mode": "blocking",
        "conversation_id": "",
        "user": DIFY_USER,
        "files": [
            {
                "type": "document",
                "transfer_method": "local_file",
                "upload_file_id": upload_file_id,
            }
        ],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_paper(
    paper_file: UploadFile | None = File(default=None),
    research_topic: str = Form(default=""),
    extract_metrics: str = Form(default=""),
) -> Any:
    if paper_file is None:
        return error_response("请先上传 PDF 文件。")

    validation_error = validate_pdf_upload(paper_file.filename, paper_file.content_type)
    if validation_error:
        return error_response(validation_error)

    config_error = require_dify_api_key()
    if config_error:
        return error_response(config_error, status_code=500)

    try:
        upload_file_id = upload_file_to_dify(paper_file)
        chat_payload = build_initial_chat_payload(
            upload_file_id=upload_file_id,
            research_topic=research_topic,
            extract_metrics=extract_metrics,
        )
        raw = call_dify_chat(chat_payload)
        answer, conversation_id = extract_chat_answer(raw)
        return ok_response(answer, conversation_id, raw)
    except requests.Timeout:
        return error_response("Dify 返回 504 或请求超时，请稍后重试。", status_code=504)
    except requests.RequestException as exc:
        return error_response(f"网络异常：{exc}", status_code=502)
    except DifyResponseError as exc:
        return error_response(str(exc), status_code=502)
    except ValueError:
        return error_response("Dify 返回了无法解析的 JSON。", status_code=502)


@app.post("/api/chat")
def chat(request: ChatRequest) -> Any:
    if not request.message.strip():
        return error_response("追问内容不能为空。")

    config_error = require_dify_api_key()
    if config_error:
        return error_response(config_error, status_code=500)

    payload = {
        "inputs": {},
        "query": request.message,
        "response_mode": "blocking",
        "conversation_id": request.conversation_id,
        "user": DIFY_USER,
    }

    try:
        raw = call_dify_chat(payload)
        answer, conversation_id = extract_chat_answer(raw)
        return ok_response(answer, conversation_id, raw)
    except requests.Timeout:
        return error_response("Dify 返回 504 或请求超时，请稍后重试。", status_code=504)
    except requests.RequestException as exc:
        return error_response(f"网络异常：{exc}", status_code=502)
    except DifyResponseError as exc:
        return error_response(str(exc), status_code=502)
    except ValueError:
        return error_response("Dify 返回了无法解析的 JSON。", status_code=502)


FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="assets")


if FRONTEND_DIST.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> Any:
        if full_path.startswith("api/"):
            return error_response("接口不存在。", status_code=404)

        requested_path = FRONTEND_DIST / full_path
        if full_path and requested_path.is_file():
            return FileResponse(requested_path)

        return FileResponse(FRONTEND_DIST / "index.html")

