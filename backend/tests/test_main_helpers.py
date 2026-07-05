import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from main import (  # noqa: E402
    DifyResponseError,
    extract_chat_answer,
    extract_dify_error_message,
    validate_pdf_upload,
)


class DummyResponse:
    def __init__(self, status_code=500, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_validate_pdf_upload_accepts_pdf_filename():
    assert validate_pdf_upload("paper.PDF", "application/pdf") is None


def test_validate_pdf_upload_rejects_non_pdf_filename():
    assert validate_pdf_upload("paper.docx", "application/pdf") == "只支持上传 PDF 文件。"


def test_extract_chat_answer_returns_answer_and_conversation_id():
    payload = {
        "answer": "# 科研分析报告\n\n内容",
        "conversation_id": "conv-123",
        "metadata": {"usage": {"total_tokens": 42}},
    }

    answer, conversation_id = extract_chat_answer(payload)

    assert answer == "# 科研分析报告\n\n内容"
    assert conversation_id == "conv-123"


def test_extract_chat_answer_raises_when_answer_missing():
    with pytest.raises(DifyResponseError, match="Dify 返回结果中没有 answer"):
        extract_chat_answer({"conversation_id": "conv-123"})


def test_extract_dify_error_message_prefers_json_message():
    response = DummyResponse(
        status_code=401,
        payload={"message": "Invalid API key"},
        text='{"message": "Invalid API key"}',
    )

    message = extract_dify_error_message(response, "Dify 对话接口调用失败")

    assert message == "Dify 对话接口调用失败：Invalid API key"


def test_extract_dify_error_message_falls_back_to_plain_text():
    response = DummyResponse(status_code=504, payload=ValueError("bad json"), text="Gateway Timeout")

    message = extract_dify_error_message(response, "Dify 对话接口调用失败")

    assert message == "Dify 对话接口调用失败：Gateway Timeout"
