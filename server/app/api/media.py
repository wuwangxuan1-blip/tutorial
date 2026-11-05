from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, Response, UploadFile

from ..models.media import MediaOut

router = APIRouter()


@router.post("/media", response_model=MediaOut, status_code=201)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    kind: str | None = Form(default=None),
) -> MediaOut:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > 110 * 1024 * 1024:
        from ..errors import ApiError
        raise ApiError(413, "MEDIA_TOO_LARGE", "上传内容超过 100 MiB 限制。")
    content = await file.read()
    result = await request.app.state.media_service.upload(
        content,
        file.content_type,
        kind,
        file.filename,
    )
    return MediaOut.model_validate(result)


@router.get("/media/{media_id}", response_model=MediaOut)
async def get_media(request: Request, media_id: str) -> MediaOut:
    result = await request.app.state.media_service.get(media_id)
    return MediaOut.model_validate(result)


@router.delete("/media/{media_id}", status_code=204)
async def delete_media(request: Request, media_id: str) -> Response:
    await request.app.state.media_service.delete(media_id)
    return Response(status_code=204)