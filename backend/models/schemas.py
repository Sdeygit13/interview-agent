from typing import Any

from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    """Request body for POST /api/interview."""

    sessionId: str = Field(..., min_length=1)
    candidate: dict[str, Any] | None = None
    message: str | None = None


class Feedback(BaseModel):
    """Structured feedback returned when the interview is complete."""

    summary: str
    strengths: list[str]
    gaps: list[str]
    next: list[str]


class InterviewResponse(BaseModel):
    """Response returned by POST /api/interview."""

    reply: str
    done: bool
    feedback: Feedback | None = None