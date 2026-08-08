import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agent.evaluator import AnswerEvaluator
from backend.agent.feedback import FeedbackGenerator
from backend.agent.interviewer import Interviewer
from backend.agent.planner import InterviewPlanner
from backend.services.llm import LLMService
from backend.services.session import SessionManager


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CURRICULUM_PATH = BASE_DIR / "data" / "curriculum.json"
CANDIDATES_PATH = BASE_DIR / "data" / "candidates.json"


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="The Interview Agent",
    description=(
        "AI-powered adaptive technical interview agent "
        "for the ABTalks AI Cohort."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD CURRICULUM
# ============================================================

try:
    with open(
        CURRICULUM_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        curriculum = json.load(file)

except FileNotFoundError as exc:
    raise RuntimeError(
        f"Curriculum file not found: {CURRICULUM_PATH}"
    ) from exc

except json.JSONDecodeError as exc:
    raise RuntimeError(
        f"Invalid curriculum JSON: {CURRICULUM_PATH}"
    ) from exc


# ============================================================
# LOAD CANDIDATES
# ============================================================

try:
    with open(
        CANDIDATES_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        candidates_data = json.load(file)

except FileNotFoundError as exc:
    raise RuntimeError(
        f"Candidates file not found: {CANDIDATES_PATH}"
    ) from exc

except json.JSONDecodeError as exc:
    raise RuntimeError(
        f"Invalid candidates JSON: {CANDIDATES_PATH}"
    ) from exc


# ============================================================
# BUILD CANDIDATE LOOKUP
# ============================================================

candidate_list = candidates_data.get(
    "candidates",
    []
)

if not isinstance(candidate_list, list):
    raise RuntimeError(
        "Invalid candidates.json format: "
        "'candidates' must be a list."
    )


candidates: dict[str, dict[str, Any]] = {}

for candidate in candidate_list:

    if not isinstance(candidate, dict):
        continue

    member = candidate.get("member", {})

    if not isinstance(member, dict):
        continue

    candidate_id = member.get("id")

    if not candidate_id:
        continue

    candidates[str(candidate_id).strip().upper()] = candidate


print(
    f"Loaded {len(candidates)} candidates "
    f"from {CANDIDATES_PATH}"
)


# ============================================================
# SERVICES
# ============================================================

sessions = SessionManager()

llm = LLMService()

planner = InterviewPlanner(
    curriculum=curriculum
)

evaluator = AnswerEvaluator(
    planner=planner,
    llm=llm,
    sessions=sessions,
)

interviewer = Interviewer(
    planner=planner,
    llm=llm,
    evaluator=evaluator,
    sessions=sessions,
)

feedback_generator = FeedbackGenerator(
    llm=llm,
    sessions=sessions,
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class InterviewRequest(BaseModel):
    """
    Request body for POST /api/interview.

    First request:
        sessionId + candidate

    Subsequent requests:
        sessionId + message
    """

    sessionId: str = Field(
        ...,
        min_length=1,
        description="Unique interview session ID.",
    )

    candidate: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Candidate profile. Required when "
            "starting a new interview."
        ),
    )

    message: str | None = Field(
        default=None,
        description=(
            "Candidate's latest interview answer."
        ),
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================

class FeedbackResponse(BaseModel):
    """
    Final structured interview feedback.
    """

    summary: str
    strengths: list[str]
    gaps: list[str]
    next: list[str]


class InterviewResponse(BaseModel):
    """
    Response returned by POST /api/interview.
    """

    reply: str
    done: bool
    feedback: FeedbackResponse | None = None


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root() -> dict[str, str]:
    """
    Basic API information.
    """

    return {
        "message": "The Interview Agent API is running.",
        "status": "healthy",
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {
        "status": "ok",
    }


# ============================================================
# CANDIDATE LOOKUP ENDPOINT
# ============================================================

@app.get(
    "/api/candidates/{candidate_id}"
)
def get_candidate(
    candidate_id: str,
) -> dict[str, Any]:
    """
    Retrieve a candidate using their candidate ID.

    Example:

        GET /api/candidates/CAND-007
    """

    normalized_id = candidate_id.strip().upper()

    if not normalized_id:
        raise HTTPException(
            status_code=400,
            detail="Candidate ID cannot be empty.",
        )

    candidate = candidates.get(
        normalized_id
    )

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Candidate '{normalized_id}' "
                "was not found."
            ),
        )

    return candidate


# ============================================================
# MAIN INTERVIEW ENDPOINT
# ============================================================

@app.post(
    "/api/interview",
    response_model=InterviewResponse,
)
def interview(
    request: InterviewRequest,
) -> InterviewResponse:

    session_id = request.sessionId.strip()

    # --------------------------------------------------------
    # Validate session ID
    # --------------------------------------------------------

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="sessionId cannot be empty.",
        )

    # --------------------------------------------------------
    # Check existing session
    # --------------------------------------------------------

    session = sessions.get_session(
        session_id
    )

    # ========================================================
    # NEW INTERVIEW
    # ========================================================

    if session is None:

        if request.candidate is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "candidate is required when "
                    "starting a new interview."
                ),
            )

        try:

            question = interviewer.start_interview(
                session_id=session_id,
                candidate=request.candidate,
            )

        except ValueError as exc:

            print(
                "START INTERVIEW VALUE ERROR:",
                repr(exc),
            )

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except Exception as exc:

            print(
                "START INTERVIEW ERROR:",
                repr(exc),
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Start interview error: {str(exc)}"
                ),
            ) from exc

        return InterviewResponse(
            reply=(
                "Welcome. Let's begin your interview.\n\n"
                + str(question)
            ),
            done=False,
            feedback=None,
        )

    # ========================================================
    # COMPLETED INTERVIEW
    # ========================================================

    if session.completed:

        try:

            feedback = (
                feedback_generator.generate_feedback(
                    session_id=session_id
                )
            )

            formatted_feedback = _format_feedback(
                feedback
            )

        except Exception as exc:

            print(
                "FEEDBACK ERROR:",
                repr(exc),
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Feedback generation error: "
                    f"{str(exc)}"
                ),
            ) from exc

        return InterviewResponse(
            reply="Interview completed.",
            done=True,
            feedback=formatted_feedback,
        )

    # ========================================================
    # EXISTING INTERVIEW — PROCESS ANSWER
    # ========================================================

    if request.message is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "message is required after "
                "the interview has started."
            ),
        )

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="message cannot be empty.",
        )

    try:

        reply = interviewer.process_answer(
            session_id=session_id,
            answer=message,
        )

    except ValueError as exc:

        print(
            "PROCESS ANSWER VALUE ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        print(
            "PROCESS ANSWER ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Process answer error: {str(exc)}"
            ),
        ) from exc

    # ========================================================
    # CHECK COMPLETION
    # ========================================================

    session = sessions.get_session(
        session_id
    )

    if (
        session is not None
        and session.completed
    ):

        try:

            feedback = (
                feedback_generator.generate_feedback(
                    session_id=session_id
                )
            )

            formatted_feedback = _format_feedback(
                feedback
            )

        except Exception as exc:

            print(
                "FINAL FEEDBACK ERROR:",
                repr(exc),
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Final feedback error: "
                    f"{str(exc)}"
                ),
            ) from exc

        return InterviewResponse(
            reply="Interview completed.",
            done=True,
            feedback=formatted_feedback,
        )

    # ========================================================
    # CONTINUE INTERVIEW
    # ========================================================

    return InterviewResponse(
        reply=str(reply),
        done=False,
        feedback=None,
    )


# ============================================================
# FEEDBACK FORMATTER
# ============================================================

def _format_feedback(
    feedback: dict[str, Any],
) -> FeedbackResponse:
    """
    Convert internal feedback into the public API format.
    """

    summary = (
        feedback.get("interviewSummary")
        or feedback.get("overallAssessment")
        or "Interview completed."
    )

    strengths = feedback.get(
        "strengths",
        [],
    )

    gaps = feedback.get(
        "knowledgeGaps",
        [],
    )

    recommendations = feedback.get(
        "recommendations",
        [],
    )

    return FeedbackResponse(
        summary=str(summary),

        strengths=[
            str(item)
            for item in strengths
        ],

        gaps=[
            str(item)
            for item in gaps
        ],

        next=[
            str(item)
            for item in recommendations
        ],
    )


# ============================================================
# DEVELOPMENT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )