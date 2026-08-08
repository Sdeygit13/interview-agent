from typing import Any

from backend.services.llm import LLMService
from backend.services.session import InterviewSession, SessionManager


class FeedbackGenerator:
    """
    Generates structured end-of-interview feedback.

    The feedback is based on:
        - Candidate profile
        - Conversation history
        - Answer evaluations
        - Strengths
        - Knowledge gaps
        - Topic-wise performance
    """

    def __init__(
        self,
        llm: LLMService,
        sessions: SessionManager,
    ) -> None:
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
        Build the feedback-generation system prompt.
        """

        candidate = session.candidate
        member = candidate.get("member", {})

        name = member.get(
            "name",
            "Candidate",
        )

        role = member.get(
            "jobRole",
            "Technical Candidate",
        )

        return f"""
You are a senior technical interviewer providing final
feedback after a technical AI engineering interview.

Candidate:
- Name: {name}
- Role: {role}

Your feedback must be:
- honest
- constructive
- specific
- actionable
- technically grounded

Do not invent information that was not demonstrated during
the interview.

Distinguish between:
- demonstrated knowledge
- partial understanding
- knowledge gaps
- areas requiring further practice

Return ONLY valid JSON with exactly this structure:

{{
  "overallScore": 0,
  "overallAssessment": "",
  "strengths": [],
  "knowledgeGaps": [],
  "recommendations": [],
  "topicPerformance": [],
  "interviewSummary": ""
}}

Rules:

- overallScore must be a number from 0 to 10.
- overallAssessment should be a concise assessment of the
  candidate's overall technical performance.
- strengths should contain specific demonstrated strengths.
- knowledgeGaps should contain specific areas that need
  improvement.
- recommendations should provide practical next steps.
- topicPerformance must contain one object for each topic
  evaluated.
- interviewSummary should summarize the interview in a
  professional manner.
- Do not include markdown.
- Do not include additional JSON fields.
""".strip()

    # =========================================================
    # BUILD INTERVIEW CONTEXT
    # =========================================================

    def _build_interview_context(
        self,
        session: InterviewSession,
    ) -> str:
        """
        Convert the session data into context for the LLM.
        """

        evaluations_text = []

        for index, evaluation in enumerate(
            session.evaluations,
            start=1,
        ):
            evaluations_text.append(
                f"""
Evaluation {index}:
Topic: {evaluation.get("topic", "Unknown")}
Day: {evaluation.get("day", "Unknown")}
Score: {evaluation.get("score", 0)}

Strengths:
{self._format_list(evaluation.get("strengths", []))}

Gaps:
{self._format_list(evaluation.get("gaps", []))}

Follow-up needed:
{evaluation.get("followUpNeeded", False)}

Summary:
{evaluation.get("summary", "")}
""".strip()
            )

        conversation_text = []

        for message in session.conversation:
            role = message.get(
                "role",
                "unknown",
            )

            content = message.get(
                "content",
                "",
            )

            conversation_text.append(
                f"{role.upper()}: {content}"
            )

        return f"""
Candidate:
{session.candidate}

Topics covered:
{self._format_list(session.topics_covered)}

Recorded strengths:
{self._format_list(session.strengths)}

Recorded knowledge gaps:
{self._format_list(session.gaps)}

Interview evaluations:
{"\n\n".join(evaluations_text)}

Interview conversation:
{"\n".join(conversation_text)}
""".strip()

    # =========================================================
    # GENERATE FEEDBACK
    # =========================================================

    def generate_feedback(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """
        Generate final structured feedback for an interview.
        """

        session = self.sessions.get_session(
            session_id,
        )

        if session is None:
            raise ValueError(
                f"Interview session '{session_id}' does not exist."
            )

        if not session.evaluations:
            raise ValueError(
                "Cannot generate feedback before at least "
                "one answer has been evaluated."
            )

        system_prompt = self._build_system_prompt(
            session,
        )

        interview_context = self._build_interview_context(
            session,
        )

        user_prompt = f"""
Generate final technical interview feedback from the
following interview data.

{interview_context}

Return only the required JSON object.
""".strip()

        feedback = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        feedback = self._validate_feedback(
            feedback,
            session,
        )

        return feedback

    # =========================================================
    # VALIDATE FEEDBACK
    # =========================================================

    def _validate_feedback(
        self,
        feedback: dict[str, Any],
        session: InterviewSession,
    ) -> dict[str, Any]:
        """
        Validate and normalize the LLM's feedback response.
        """

        if not isinstance(feedback, dict):
            raise RuntimeError(
                "Feedback generator returned an invalid response."
            )

        required_fields = {
            "overallScore",
            "overallAssessment",
            "strengths",
            "knowledgeGaps",
            "recommendations",
            "topicPerformance",
            "interviewSummary",
        }

        missing_fields = (
            required_fields - feedback.keys()
        )

        if missing_fields:
            raise RuntimeError(
                "Feedback response is missing fields: "
                + ", ".join(
                    sorted(missing_fields)
                )
            )

        # -----------------------------------------------------
        # Overall score
        # -----------------------------------------------------

        try:
            score = float(
                feedback["overallScore"]
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise RuntimeError(
                "Overall score must be numeric."
            ) from exc

        score = max(
            0.0,
            min(10.0, score),
        )

        feedback["overallScore"] = round(
            score,
            1,
        )

        # -----------------------------------------------------
        # Text fields
        # -----------------------------------------------------

        feedback["overallAssessment"] = str(
            feedback["overallAssessment"]
        ).strip()

        feedback["interviewSummary"] = str(
            feedback["interviewSummary"]
        ).strip()

        # -----------------------------------------------------
        # Lists
        # -----------------------------------------------------

        feedback["strengths"] = self._clean_string_list(
            feedback["strengths"]
        )

        feedback["knowledgeGaps"] = self._clean_string_list(
            feedback["knowledgeGaps"]
        )

        feedback["recommendations"] = self._clean_string_list(
            feedback["recommendations"]
        )

        # -----------------------------------------------------
        # Topic performance
        # -----------------------------------------------------

        feedback["topicPerformance"] = (
            self._validate_topic_performance(
                feedback["topicPerformance"]
            )
        )

        return feedback

    # =========================================================
    # TOPIC PERFORMANCE VALIDATION
    # =========================================================

    def _validate_topic_performance(
        self,
        topics: Any,
    ) -> list[dict[str, Any]]:
        """
        Validate topic-wise performance objects.
        """

        if not isinstance(
            topics,
            list,
        ):
            return []

        cleaned_topics = []

        for topic in topics:
            if not isinstance(
                topic,
                dict,
            ):
                continue

            topic_name = str(
                topic.get(
                    "topic",
                    "Unknown",
                )
            ).strip()

            day = topic.get(
                "day",
                None,
            )

            try:
                score = float(
                    topic.get(
                        "score",
                        0,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                score = 0.0

            score = max(
                0.0,
                min(10.0, score),
            )

            assessment = str(
                topic.get(
                    "assessment",
                    "",
                )
            ).strip()

            cleaned_topics.append(
                {
                    "topic": topic_name,
                    "day": day,
                    "score": round(
                        score,
                        1,
                    ),
                    "assessment": assessment,
                }
            )

        return cleaned_topics

    # =========================================================
    # UTILITY
    # =========================================================

    @staticmethod
    def _clean_string_list(
        value: Any,
    ) -> list[str]:
        """
        Convert an arbitrary value into a clean list of strings.
        """

        if not isinstance(
            value,
            list,
        ):
            return []

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    @staticmethod
    def _format_list(
        items: Any,
    ) -> str:
        """
        Format a list for an LLM prompt.
        """

        if not items:
            return "- None"

        if not isinstance(
            items,
            list,
        ):
            return f"- {items}"

        return "\n".join(
            f"- {item}"
            for item in items
        )


# =============================================================
# FACTORY
# =============================================================

def create_feedback_generator(
    llm: LLMService,
    sessions: SessionManager,
) -> FeedbackGenerator:
    """
    Convenience factory for creating a feedback generator.
    """

    return FeedbackGenerator(
        llm=llm,
        sessions=sessions,
    )