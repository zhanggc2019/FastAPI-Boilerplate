import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from loguru import logger

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

    def _build_url(self, chat_id: str | None) -> str:
        chat_id = chat_id or self.default_chat_id

        if "{chat_id}" in self.chat_path and not chat_id:
            raise BadRequestException("Missing chat_id for RAGFlow request")

        path = self.chat_path.format(chat_id=chat_id)
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
        messages: list[dict[str, str]] | None,
        stream: bool,
        extra_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        # OpenAI 兼容接口
        if "/chats_openai/" in self.chat_path or "/chat/completions" in self.chat_path:
            resolved_messages = messages or [{"role": "user", "content": question or ""}]
            payload: dict[str, Any] = {
                "model": "model",  # RAGFlow API 需要 model 参数
                "messages": resolved_messages,
                "stream": stream,
            }
            if extra_body:
                payload["extra_body"] = extra_body
                if "reference" in extra_body:
                    payload["reference"] = extra_body["reference"]
            return payload

        # Chat assistant 接口
        resolved_question = question
        if not resolved_question and messages:
            resolved_question = messages[-1].get("content")
        payload = {
            "question": resolved_question or "",
            "stream": stream,
        }
        if extra_body:
            if "metadata_condition" in extra_body:
                payload["metadata_condition"] = extra_body["metadata_condition"]
            if "reference" in extra_body:
                payload["reference"] = extra_body["reference"]
        return payload

    @staticmethod
    def _resolve_question(question: str | None, messages: list[dict[str, str]] | None) -> str:
        if question:
            return question
        if messages:
            return messages[-1].get("content", "")
        return ""

    async def _get_chat(self, chat_id: str) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/api/v1/chats"
        params = {"page": 1, "page_size": 1, "id": chat_id}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=self._headers())
        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("RAGFlow API request timeout") from err
        except httpx.RequestError as err:
            raise ExternalServiceException(f"RAGFlow API request failed: {str(err)}") from err

        if response.status_code >= 400:
            detail = response.text.strip()
            raise ExternalServiceException(f"RAGFlow API error: {response.status_code} {detail}")

        data = response.json()
        if isinstance(data, dict) and data.get("code") == 0 and isinstance(data.get("data"), list):
            return data["data"][0] if data["data"] else {}
        return data.get("data", {}) if isinstance(data.get("data"), dict) else {}

    async def _retrieve_reference(
        self, question: str, dataset_ids: list[str], metadata_condition: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        if not question or not dataset_ids:
            logger.warning("[RAGFlow] fallback retrieval skipped: question or dataset_ids missing")
            return None

        url = f"{self.base_url.rstrip('/')}/api/v1/retrieval"
        payload: dict[str, Any] = {
            "question": question,
            "dataset_ids": dataset_ids,
            "page": 1,
            "page_size": 6,
        }
        if metadata_condition:
            payload["metadata_condition"] = metadata_condition

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

        data = response.json()
        if not isinstance(data, dict) or data.get("code") != 0:
            logger.warning(f"[RAGFlow] retrieval failed or bad code: {data}")
            return None

        data_obj = data.get("data") if isinstance(data.get("data"), dict) else {}
        chunks = data_obj.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            logger.warning("[RAGFlow] retrieval got empty chunks")
            return None

        doc_aggs = data_obj.get("doc_aggs") if isinstance(data_obj.get("doc_aggs"), list) else []
        reference_chunks = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            reference_chunks.append(
                {
                    "id": chunk.get("id"),
                    "content": chunk.get("content"),
                    "document_id": chunk.get("document_id"),
                    "document_name": chunk.get("document_keyword"),
                    "dataset_id": chunk.get("kb_id"),
                    "image_id": chunk.get("image_id"),
                    "positions": chunk.get("positions"),
                    "similarity": chunk.get("similarity"),
                    "vector_similarity": chunk.get("vector_similarity"),
                    "term_similarity": chunk.get("term_similarity"),
                }
            )

        return {
            "total": data_obj.get("total"),
            "chunks": reference_chunks,
            "doc_aggs": doc_aggs,
        }

    async def ask(
        self,
        question: str | None = None,
        messages: list[dict[str, str]] | None = None,
        chat_id: str | None = None,
        stream: bool = False,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not messages and not question:
            raise BadRequestException("Question or messages is required")
        if stream:
            raise BadRequestException("Streaming responses are not supported by this endpoint")

        payload = self._build_payload(question, messages, stream, extra_body)
        url = self._build_url(chat_id=chat_id)
        resolved_question = self._resolve_question(question, messages)

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
        reference = None
        if isinstance(data, dict):
            reference = data.get("reference")
            if not reference and isinstance(data.get("data"), dict):
                reference = data["data"].get("reference")
        if not reference and resolved_question:
            try:
                chat_info = await self._get_chat(chat_id or self.default_chat_id)
                dataset_ids = chat_info.get("dataset_ids") if isinstance(chat_info, dict) else None
                if isinstance(dataset_ids, list) and dataset_ids:
                    reference = await self._retrieve_reference(
                        resolved_question,
                        dataset_ids,
                        metadata_condition=extra_body.get("metadata_condition") if extra_body else None,
                    )
                else:
                    logger.warning("[RAGFlow] no dataset_ids found for chat, cannot build reference fallback")
            except Exception as err:
                logger.warning(f"[RAGFlow] fallback reference failed: {err}")
        return {"answer": answer, "session_id": session_id, "reference": reference, "raw": data}

    async def ask_stream(
        self,
        question: str | None = None,
        messages: list[dict[str, str]] | None = None,
        chat_id: str | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        if not messages and not question:
            raise BadRequestException("Question or messages is required")

        payload = self._build_payload(question, messages, True, extra_body)
        url = self._build_url(chat_id=chat_id)
        resolved_question = self._resolve_question(question, messages)

        # 调试日志：查看实际发送的请求
        logger.info(f"[RAGFlow] 发送请求到: {url}")
        logger.info(f"[RAGFlow] 请求 payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        # 设置合理的超时时间：连接超时 30 秒，读取超时 120 秒
        timeout = httpx.Timeout(30.0, read=120.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload, headers=self._headers()) as response:
                    if response.status_code >= 400:
                        detail = await response.aread()
                        error_msg = f"RAGFlow API error: {response.status_code} {detail.decode('utf-8', errors='ignore')}"
                        # 返回错误消息而不是抛出异常，确保前端能收到
                        yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
                        return

                    # 直接透传 RAGFlow 的 SSE 流
                    # RAGFlow 返回格式: data:{json}\n 或 data:{json}\n\n
                    buffer = ""
                    line_count = 0
                    all_lines = []
                    saw_reference = False
                    try:
                        async for chunk in response.aiter_bytes():
                            if not chunk:
                                continue
                            # 解码字节并添加到缓冲区
                            buffer += chunk.decode("utf-8", errors="ignore")

                            # 按行分割处理，保留最后一个可能不完整的行
                            lines = buffer.split("\n")
                            buffer = lines.pop() if lines else ""

                            for line in lines:
                                line = line.rstrip("\r")
                                # 跳过空行
                                if not line.strip():
                                    continue
                                line_count += 1
                                all_lines.append(line)

                                # RAGFlow 返回 data:{...} 格式，直接透传
                                # 确保以 \n\n 结尾（SSE 标准格式）
                                yield line + "\n\n"
                                if line.startswith("data:"):
                                    data_str = line.replace("data:", "", 1).strip()
                                    try:
                                        payload_json = json.loads(data_str)
                                        reference = (
                                            payload_json.get("reference")
                                            or payload_json.get("data", {}).get("reference")
                                            or payload_json.get("choices", [{}])[0]
                                            .get("delta", {})
                                            .get("reference")
                                        )
                                        if reference:
                                            saw_reference = True
                                    except json.JSONDecodeError:
                                        pass

                        logger.info(f"[RAGFlow] 总共收到 {line_count} 行数据")
                        logger.info(f"[RAGFlow] 所有数据行:")
                        for i, line in enumerate(all_lines, 1):
                            # 截断太长的行
                            display_line = line if len(line) <= 300 else line[:300] + "..."
                            logger.info(f"  [{i}] {display_line}")

                    except httpx.RemoteProtocolError:
                        # 连接被提前关闭，但可能已经收到了部分数据
                        # 这不是致命错误，继续处理缓冲区中的数据
                        pass

                    # 处理缓冲区剩余的数据
                    if buffer.strip():
                        yield buffer.rstrip("\r") + "\n\n"

                    if not saw_reference and resolved_question:
                        try:
                            chat_info = await self._get_chat(chat_id or self.default_chat_id)
                            dataset_ids = chat_info.get("dataset_ids") if isinstance(chat_info, dict) else None
                            if isinstance(dataset_ids, list) and dataset_ids:
                                reference = await self._retrieve_reference(
                                    resolved_question,
                                    dataset_ids,
                                    metadata_condition=extra_body.get("metadata_condition") if extra_body else None,
                                )
                                if reference:
                                    yield f"data: {json.dumps({'reference': reference}, ensure_ascii=False)}\n\n"
                            else:
                                logger.warning("[RAGFlow] no dataset_ids found for chat, cannot build reference fallback")
                        except Exception as err:
                            logger.warning(f"[RAGFlow] fallback reference failed: {err}")

                    # 发送流结束标记
                    yield "data: [DONE]\n\n"

        except httpx.TimeoutException as err:
            error_msg = f"RAGFlow API timeout: {str(err)}"
            yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
        except httpx.RequestError as err:
            error_msg = f"RAGFlow API request failed: {str(err)}"
            yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"
        except Exception as err:
            error_msg = f"Unexpected error: {str(err)}"
            yield f"data: {{\"error\": \"{error_msg}\"}}\n\n"

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
        data_obj = data.get("data") if isinstance(data.get("data"), dict) else {}
        chunks = data.get("chunks") or data_obj.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            return data

        chunk = chunks[0]
        doc = data_obj.get("doc") if isinstance(data_obj.get("doc"), dict) else {}
        document_name = (
            chunk.get("document_name")
            or chunk.get("docnm_kwd")
            or doc.get("name")
            or doc.get("location")
        )
        doc_type = chunk.get("doc_type") or doc.get("type")
        download_url = f"/api/v1/assistant/documents/{dataset_id}/{document_id}/download"
        chunk = {
            **chunk,
            "document": doc,
            "document_name": document_name,
            "title": chunk.get("title") or document_name,
            "doc_type": doc_type,
            "download_url": chunk.get("download_url") or download_url,
        }
        return chunk

    async def get_document(self, dataset_id: str, document_id: str) -> dict[str, Any]:
        if not dataset_id or not document_id:
            raise BadRequestException("dataset_id and document_id are required")

        url = f"{self.base_url.rstrip('/')}/api/v1/datasets/{dataset_id}/documents"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params={"id": document_id, "page": 1, "page_size": 1}, headers=self._headers())
        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("RAGFlow API request timeout") from err
        except httpx.RequestError as err:
            raise ExternalServiceException(f"RAGFlow API request failed: {str(err)}") from err

        if response.status_code >= 400:
            detail = response.text.strip()
            raise ExternalServiceException(f"RAGFlow API error: {response.status_code} {detail}")

        data = response.json()
        docs = data.get("data", {}).get("docs") if isinstance(data.get("data"), dict) else None
        raw = docs[0] if isinstance(docs, list) and docs else None
        if not isinstance(raw, dict):
            return {}

        document_name = raw.get("name") or raw.get("location")
        doc_type = raw.get("type")
        download_url = f"/api/v1/assistant/documents/{dataset_id}/{document_id}/download"
        return {
            "document_name": document_name,
            "title": document_name,
            "download_url": download_url,
            "doc_type": doc_type,
            "raw": raw,
        }

    async def download_document_stream(self, dataset_id: str, document_id: str) -> AsyncGenerator[bytes, None]:
        if not dataset_id or not document_id:
            raise BadRequestException("dataset_id and document_id are required")

        url = f"{self.base_url.rstrip('/')}/api/v1/datasets/{dataset_id}/documents/{document_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("GET", url, headers=self._headers()) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    error_msg = detail.decode("utf-8", errors="ignore")
                    raise ExternalServiceException(f"RAGFlow API error: {response.status_code} {error_msg}")
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield chunk
