import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.core.config import config
from app.core.exceptions import (
    BadRequestException,
    ExternalServiceException,
    ExternalServiceTimeoutException,
)


class RagflowService:
    """RAGFlow knowledge base Q&A service."""

    def __init__(self) -> None:
        self.base_url = config.RAGFLOW_BASE_URL
        self.chat_path = config.RAGFLOW_CHAT_PATH
        self.api_key = config.RAGFLOW_API_KEY
        self.api_key_header = config.RAGFLOW_API_KEY_HEADER
        self.api_key_prefix = config.RAGFLOW_API_KEY_PREFIX
        self.timeout = config.RAGFLOW_TIMEOUT
        self.default_chat_id = config.RAGFLOW_CHAT_ID
        self.default_kb_id = config.RAGFLOW_KB_ID
        self.default_model = config.RAGFLOW_MODEL

    def _build_url(self, chat_id: str | None, kb_id: str | None) -> str:
        chat_id = chat_id or self.default_chat_id
        kb_id = kb_id or self.default_kb_id

        if "{chat_id}" in self.chat_path and not chat_id:
            raise BadRequestException("Missing chat_id for RAGFlow request")
        if "{kb_id}" in self.chat_path and not kb_id:
            raise BadRequestException("Missing kb_id for RAGFlow request")

        path = self.chat_path.format(chat_id=chat_id, kb_id=kb_id)
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            token = f"{self.api_key_prefix} {self.api_key}".strip()
            headers[self.api_key_header] = token
        return headers

    @staticmethod
    def _extract_answer(payload: dict[str, Any]) -> str:
        if isinstance(payload.get("answer"), str):
            return payload["answer"]
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("answer"), str):
            return data["answer"]
        if isinstance(payload.get("response"), str):
            return payload["response"]
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                return message["content"]
        return ""

    @staticmethod
    def _extract_session_id(payload: dict[str, Any]) -> str | None:
        if isinstance(payload.get("session_id"), str):
            return payload["session_id"]
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("session_id"), str):
            return data["session_id"]
        return None

    def _build_payload(
        self,
        question: str | None,
        model: str | None,
        messages: list[dict[str, str]] | None,
        stream: bool,
        kb_id: str | None,
        extra_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        resolved_messages = messages or [{"role": "user", "content": question or ""}]
        payload: dict[str, Any] = {
            "model": model or self.default_model or "model",
            "messages": resolved_messages,
            "stream": stream,
        }
        if extra_body:
            payload["extra_body"] = extra_body
        if kb_id or self.default_kb_id:
            payload.setdefault("extra_body", {})
            payload["extra_body"]["kb_id"] = kb_id or self.default_kb_id
        return payload

    async def ask(
        self,
        question: str | None = None,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        chat_id: str | None = None,
        kb_id: str | None = None,
        stream: bool = False,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not messages and not question:
            raise BadRequestException("Question or messages is required")
        if stream:
            raise BadRequestException("Streaming responses are not supported by this endpoint")

        payload = self._build_payload(question, model, messages, stream, kb_id, extra_body)

        url = self._build_url(chat_id=chat_id, kb_id=kb_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("RAGFlow API request timeout") from err
        except httpx.RequestError as err:
            raise ExternalServiceException(f"RAGFlow API request failed: {str(err)}") from err

        if response.status_code >= 400:
            detail = response.text.strip()
            raise ExternalServiceException(f"RAGFlow API error: {response.status_code} {detail}")

        try:
            data = response.json()
        except ValueError:
            data = {"raw": response.text}

        answer = self._extract_answer(data)
        if not answer:
            answer = json.dumps(data, ensure_ascii=True)

        session_id = self._extract_session_id(data)
        return {"answer": answer, "session_id": session_id, "raw": data}

    def ask_stream(
        self,
        question: str | None = None,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        chat_id: str | None = None,
        kb_id: str | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> AsyncGenerator[bytes, None]:
        if not messages and not question:
            raise BadRequestException("Question or messages is required")

        payload = self._build_payload(question, model, messages, True, kb_id, extra_body)
        url = self._build_url(chat_id=chat_id, kb_id=kb_id)

        async def _generator() -> AsyncGenerator[bytes, None]:
            timeout = httpx.Timeout(self.timeout, read=None)

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", url, json=payload, headers=self._headers()) as response:
                        if response.status_code >= 400:
                            detail = await response.aread()
                            raise ExternalServiceException(
                                f"RAGFlow API error: {response.status_code} {detail.decode('utf-8', errors='ignore')}"
                            )
                        async for line in response.aiter_lines():
                            if line == "":
                                yield b"\n"
                            else:
                                yield (line + "\n").encode("utf-8")
            except httpx.TimeoutException as err:
                raise ExternalServiceTimeoutException("RAGFlow API request timeout") from err
            except httpx.RequestError as err:
                raise ExternalServiceException(f"RAGFlow API request failed: {str(err)}") from err

        return _generator()

    async def get_chunk(self, dataset_id: str, document_id: str, chunk_id: str) -> dict[str, Any]:
        if not dataset_id or not document_id or not chunk_id:
            raise BadRequestException("dataset_id, document_id and chunk_id are required")

        url = f"{self.base_url.rstrip('/')}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params={"id": chunk_id}, headers=self._headers())
        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("RAGFlow API request timeout") from err
        except httpx.RequestError as err:
            raise ExternalServiceException(f"RAGFlow API request failed: {str(err)}") from err

        if response.status_code >= 400:
            detail = response.text.strip()
            raise ExternalServiceException(f"RAGFlow API error: {response.status_code} {detail}")

        data = response.json()
        chunks = data.get("chunks") or data.get("data", {}).get("chunks")
        if isinstance(chunks, list) and chunks:
            return chunks[0]
        return data
