import re
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.factory import Factory
from app.schemas.requests.ragflow import RagflowAskRequest
from app.schemas.responses.ragflow import RagflowAskResponse
from app.services import RagflowService

ragflow_router = APIRouter()


def build_content_disposition(filename: str) -> str:
    ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("_") or "document"
    if filename.isascii():
        return f'attachment; filename="{filename}"'
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


@ragflow_router.post("/ask", response_model=RagflowAskResponse)
async def ask_ragflow(
    payload: RagflowAskRequest,
    ragflow_service: RagflowService = Depends(Factory().get_ragflow_service),
):
    if payload.stream:
        stream = ragflow_service.ask_stream(
            question=payload.question,
            messages=[message.model_dump() for message in payload.messages] if payload.messages else None,
            chat_id=payload.chat_id,
            extra_body=payload.extra_body,
        )
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    response = await ragflow_service.ask(
        question=payload.question,
        messages=[message.model_dump() for message in payload.messages] if payload.messages else None,
        chat_id=payload.chat_id,
        stream=False,
        extra_body=payload.extra_body,
    )
    return RagflowAskResponse.model_validate(response)


@ragflow_router.get("/chunks/{dataset_id}/{document_id}/{chunk_id}")
async def get_chunk_detail(
    dataset_id: str,
    document_id: str,
    chunk_id: str,
    ragflow_service: RagflowService = Depends(Factory().get_ragflow_service),
):
    return await ragflow_service.get_chunk(dataset_id=dataset_id, document_id=document_id, chunk_id=chunk_id)


@ragflow_router.get("/documents/{dataset_id}/{document_id}/download")
async def download_document(
    dataset_id: str,
    document_id: str,
    ragflow_service: RagflowService = Depends(Factory().get_ragflow_service),
):
    document = await ragflow_service.get_document(dataset_id=dataset_id, document_id=document_id)
    filename = (document.get("document_name") if isinstance(document, dict) else None) or "document"
    stream = ragflow_service.download_document_stream(dataset_id=dataset_id, document_id=document_id)
    headers = {"Content-Disposition": build_content_disposition(filename)}
    return StreamingResponse(stream, media_type="application/octet-stream", headers=headers)
