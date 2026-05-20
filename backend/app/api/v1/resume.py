import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.agents.harness import harness
from app.middleware.auth import get_current_user
from app.schemas.resume import ResumeExtractRequest
from app.config import settings

router = APIRouter()


async def save_upload(upload: UploadFile | None) -> str:
    if not upload or not upload.filename:
        return ""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(upload.filename)[1]
    path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(path, "wb") as f:
        f.write(await upload.read())
    return path


@router.post("/extract")
async def extract_resume(
    input_text: str = Form(""),
    doc: UploadFile = File(None),
    image: UploadFile = File(None),
    user: dict = Depends(get_current_user),
):
    result = await harness.run(
        "resume_analyzer",
        {
            "input_text": input_text,
            "file_path": await save_upload(doc),
            "image_path": await save_upload(image),
            "user_id": user["user_id"],
        },
        user_id=user["user_id"],
    )
    return result


@router.post("/supplement")
async def supplement_resume(
    req: ResumeExtractRequest,
    user: dict = Depends(get_current_user),
):
    result = await harness.run(
        "resume_analyzer",
        {
            "input_text": "",
            "supplement_text": req.supplement_text,
            "supplement_count": req.supplement_count,
            "user_profile": req.user_profile,
            "user_id": user["user_id"],
        },
        user_id=user["user_id"],
    )
    return result


@router.post("/analyze")
async def analyze_resume(
    req: ResumeExtractRequest,
    user: dict = Depends(get_current_user),
):
    """Force a full analysis with an existing user_profile (completeness forced to 100%)."""
    result = await harness.run(
        "resume_analyzer",
        {
            "input_text": json.dumps(req.user_profile or {}, ensure_ascii=False),
            "user_id": user["user_id"],
        },
        user_id=user["user_id"],
    )
    return result


import json
