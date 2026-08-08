from typing import Any

from backend.agent.planner import InterviewPlanner
from backend.services.llm import LLMService
from backend.services.session import InterviewSession, SessionManager


class AnswerEvaluator:
    """
    Evaluates candidate answers against the current
    curriculum topic and learning objectives.

    The evaluator produces structured information that can
    be used by the interviewer to decide whether to:

        - ask a follow-up question
        - move to another topic
        - record a strength
        - record a knowledge gap
    """

    def __init__(
        self,
        planner: InterviewPlanner,
        llm: LLMService,
        sessions: SessionManager,
    ) -> None:
        self.planner = planner
        self.llm = llm
        self.sessions = sessions

    # =========================================================
    # SYSTEM PROMPT
    # =========================================================

    def _build_system_prompt(
        self,
        session: InterviewSession,
    ) -> str:
        """
        Build the evaluation prompt.
        """

        candidate = session.candidate
        member = candidate.get("member", {})

        return f"""
You are a senior technical interviewer evaluating a candidate's
answer during an AI engineering interview.

Candidate:
- Name: {member.get("name", "Candidate")}
- Role: {member.get("jobRole", "Technical Candidate")}
- Experience: {member.get("yearsExperience", "unknown")} years
- Education: {member.get("education", "unknown")}

Evaluate the candidate fairly and only against the supplied
curriculum topic and learning objectives.

Do not evaluate based on unrelated knowledge.

Your evaluation must be practical and evidence-based.

Return ONLY valid JSON with exactly these fields:

{{
  "score": 0,
  "strengths": [],
  "gaps": [],
  "followUpNeeded": false,
  "followUpReason": "",
  "summary": ""
}}

Rules:

- score must be an integer from 0 to 10.
- strengths must contain concise observations supported by
  the candidate's answer.
- gaps must identify important missing, incorrect, or unclear
  technical concepts.
- followUpNeeded must be true when the answer needs deeper
  probing or clarification.
- followUpReason must explain why a follow-up is useful.
- summary must briefly describe the quality of the answer.
- Do not invent claims about what the candidate knows.
- Do not reward irrelevant information.
- A short but technically correct answer can receive a strong score.
- A confident but technically incorrect answer should not receive
  a high score.
""".strip()

    # =========================================================
    # TOPIC CONTEXT
    # =========================================================

    def _build_topic_context(
        self,
        topic: dict[str, Any],
    ) -> str:
        """
        Build the curriculum context used during evaluation.
        """

        objectives = topic.get("objectives", [])
        tools = topic.get("tools", [])

        objectives_text = "\n".join(
            f"- {objective}"
            for objective in objectives
        )

        tools_text = ", ".join(tools)

        return f"""
Curriculum Day: {topic.get("day")}
Topic: {topic.get("title")}
Type: {topic.get("type")}

Tools:
{tools_text}

Learning objectives:
{objectives_text}
""".strip()

    # =========================================================
    # EVALUATE ANSWER
    # =========================================================

    def evaluate(
        self,
        session_id: str,
        answer: str,
    ) -> dict[str, Any]:
        """
        Evaluate a candidate's answer.

        The answer is evaluated against the current interview
        topic and its curriculum objectives.
        """

        session = self.sessions.get_session(session_id)

        if session is None:
            raise ValueError(
                f"Interview session '{session_id}' does not exist."
            )

        if not answer.strip():
            raise ValueError(
                "Cannot evaluate an empty answer."
            )

        topic = self._get_current_topic(session)

        if topic is None:
            raise RuntimeError(
                "No current curriculum topic is available."
            )

        system_prompt = self._build_system_prompt(session)

        topic_context = self._build_topic_context(topic)

        user_prompt = f"""
{topic_context}

Current interview question:
{session.current_question or "No question recorded."}

Candidate answer:
{answer.strip()}

Evaluate this answer according to the curriculum objectives.
""".strip()

        evaluation = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        evaluation = self._validate_evaluation(
            evaluation,
        )

        # Add useful metadata for our application.
        evaluation["topic"] = topic.get("title", "")
        evaluation["day"] = topic.get("day")

        # Store the evaluation in session memory.
        self.sessions.add_evaluation(
            session_id=session_id,
            evaluation=evaluation,
        )

        # Store strengths and gaps for final feedback.
        self._record_learning_signals(
            session_id=session_id,
            evaluation=evaluation,
        )

        return evaluation

    # =========================================================
    # CURRENT TOPIC
    # =========================================================

    def _get_current_topic(
        self,
        session: InterviewSession,
    ) -> dict[str, Any] | None:
        """
        Retrieve the curriculum topic currently being discussed.
        """

        if not session.current_topic:
            return None

        return self.planner.get_topic_by_title(
            session.current_topic,
        )

    # =========================================================
    # VALIDATE LLM OUTPUT
    # =========================================================

    def _validate_evaluation(
        self,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize the LLM's structured evaluation.
        """

        if not isinstance(evaluation, dict):
            raise RuntimeError(
                "Evaluator returned an invalid response."
            )

        required_fields = {
            "score",
            "strengths",
            "gaps",
            "followUpNeeded",
            "followUpReason",
            "summary",
        }

        missing_fields = required_fields - evaluation.keys()

        if missing_fields:
            raise RuntimeError(
                "Evaluator response is missing fields: "
                + ", ".join(sorted(missing_fields))
            )

        # -----------------------------------------------------
        # Score
        # -----------------------------------------------------

        score = evaluation["score"]

        if isinstance(score, bool):
            raise RuntimeError(
                "Evaluator score must be an integer."
            )

        try:
            score = int(score)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "Evaluator score must be an integer."
            ) from exc

        score = max(0, min(10, score))

        evaluation["score"] = score

        # -----------------------------------------------------
        # Strengths
        # -----------------------------------------------------

        if not isinstance(
            evaluation["strengths"],
            list,
        ):
            evaluation["strengths"] = []

        evaluation["strengths"] = [
            str(item).strip()
            for item in evaluation["strengths"]
            if str(item).strip()
        ]

        # -----------------------------------------------------
        # Gaps
        # -----------------------------------------------------

        if not isinstance(
            evaluation["gaps"],
            list,
        ):
            evaluation["gaps"] = []

        evaluation["gaps"] = [
            str(item).strip()
            for item in evaluation["gaps"]
            if str(item).strip()
        ]

        # -----------------------------------------------------
        # Follow-up
        # -----------------------------------------------------

        evaluation["followUpNeeded"] = bool(
            evaluation["followUpNeeded"]
        )

        evaluation["followUpReason"] = str(
            evaluation["followUpReason"]
        ).strip()

        # -----------------------------------------------------
        # Summary
        # -----------------------------------------------------

        evaluation["summary"] = str(
            evaluation["summary"]
        ).strip()

        return evaluation

    # =========================================================
    # LEARNING SIGNALS
    # =========================================================

    def _record_learning_signals(
        self,
        session_id: str,
        evaluation: dict[str, Any],
    ) -> None:
        """
        Record strengths and knowledge gaps in the session.
        """

        for strength in evaluation.get(
            "strengths",
            [],
        ):
            self.sessions.add_strength(
                session_id=session_id,
                strength=strength,
            )

        for gap in evaluation.get(
            "gaps",
            [],
        ):
            self.sessions.add_gap(
                session_id=session_id,
                gap=gap,
            )

    # =========================================================
    # FOLLOW-UP DECISION
    # =========================================================

    def should_follow_up(
        self,
        evaluation: dict[str, Any],
    ) -> bool:
        """
        Return whether the candidate's answer needs
        a deeper follow-up question.
        """

        return bool(
            evaluation.get(
                "followUpNeeded",
                False,
            )
        )