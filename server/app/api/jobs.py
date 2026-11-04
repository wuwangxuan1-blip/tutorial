from __future__ import annotations

from fastapi import APIRouter, Request

from ..models.job import JobOut
from .sessions import job_out

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(request: Request, job_id: str) -> JobOut:
    job = await request.app.state.job_service.get_job(job_id)
    return job_out(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
async def cancel_job(request: Request, job_id: str) -> JobOut:
    job = await request.app.state.job_service.cancel(job_id)
    return job_out(job)