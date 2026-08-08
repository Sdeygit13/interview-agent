from dataclasses import dataclass, field
from typing import Any


@dataclass
class InterviewSession:
    """
    Stores all state belonging to one interview session.
    """

    session_id: str
    candidate: dict[str, Any]

    # Complete conversation history.
    conversation: list[dict[str, str]] = field(
        default_factory=list
    )

    # Current question/topic.
    current_question: str | None = None
    current_topic: str | None = None

    # Interview progress.
    question_count: int = 0
    topics_covered: list[str] = field(
        default_factory=list
    )

    # Evaluation history.
    evaluations: list[dict[str, Any]] = field(
        default_factory=list
    )

    # Aggregated learning signals from the interview.
    strengths: list[str] = field(
        default_factory=list
    )

    gaps: list[str] = field(
        default_factory=list
    )

    # Whether the interview has ended.
    completed: bool = False


class SessionManager:
    """
    In-memory manager for interview sessions.

    Persistent user accounts and long-term history are not
    required for the hackathon, so sessions are intentionally
    kept in memory.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, InterviewSession] = {}

    # =========================================================
    # CREATE / GET
    # =========================================================

    def create_session(
        self,
        session_id: str,
        candidate: dict[str, Any],
    ) -> InterviewSession:
        """
        Create a new interview session.

        Raises ValueError if the session ID already exists.
        """

        if session_id in self._sessions:
            raise ValueError(
                f"Interview session '{session_id}' already exists."
            )

        session = InterviewSession(
            session_id=session_id,
            candidate=candidate,
        )

        self._sessions[session_id] = session

        return session

    def get_session(
        self,
        session_id: str,
    ) -> InterviewSession | None:
        """
        Return a session if it exists.
        """

        return self._sessions.get(session_id)

    def delete_session(
        self,
        session_id: str,
    ) -> bool:
        """
        Delete an interview session.

        Returns True if a session was deleted.
        """

        if session_id not in self._sessions:
            return False

        del self._sessions[session_id]

        return True

    # =========================================================
    # CONVERSATION
    # =========================================================

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Add a message to the interview conversation.

        Valid roles:
            user
            assistant
        """

        session = self._require_session(
            session_id
        )

        role = role.strip()
        content = content.strip()

        if role not in {"user", "assistant"}:
            raise ValueError(
                "Message role must be 'user' or 'assistant'."
            )

        if not content:
            raise ValueError(
                "Message content cannot be empty."
            )

        session.conversation.append(
            {
                "role": role,
                "content": content,
            }
        )

    def get_conversation(
        self,
        session_id: str,
    ) -> list[dict[str, str]]:
        """
        Return the complete conversation history.
        """

        session = self._require_session(
            session_id
        )

        return list(session.conversation)

    # =========================================================
    # CURRENT QUESTION
    # =========================================================

    def set_current_question(
        self,
        session_id: str,
        question: str,
        topic: str,
    ) -> None:
        """
        Store the question currently being asked.
        """

        session = self._require_session(
            session_id
        )

        session.current_question = question.strip()
        session.current_topic = topic.strip()

    def get_current_question(
        self,
        session_id: str,
    ) -> str | None:
        """
        Return the current interview question.
        """

        session = self._require_session(
            session_id
        )

        return session.current_question

    def get_current_topic(
        self,
        session_id: str,
    ) -> str | None:
        """
        Return the current curriculum topic.
        """

        session = self._require_session(
            session_id
        )

        return session.current_topic

    # =========================================================
    # QUESTION COUNT
    # =========================================================

    def increment_question_count(
        self,
        session_id: str,
    ) -> int:
        """
        Increase the number of interviewer questions asked.

        Returns the new count.
        """

        session = self._require_session(
            session_id
        )

        session.question_count += 1

        return session.question_count

    def get_question_count(
        self,
        session_id: str,
    ) -> int:
        """
        Return the number of questions asked.
        """

        session = self._require_session(
            session_id
        )

        return session.question_count

    # =========================================================
    # TOPICS
    # =========================================================

    def add_topic(
        self,
        session_id: str,
        topic: str,
    ) -> None:
        """
        Add a curriculum topic to the covered-topic list.

        Duplicate topics are ignored.
        """

        session = self._require_session(
            session_id
        )

        topic = topic.strip()

        if not topic:
            return

        if topic not in session.topics_covered:
            session.topics_covered.append(topic)

    def get_topics_covered(
        self,
        session_id: str,
    ) -> list[str]:
        """
        Return all curriculum topics covered so far.
        """

        session = self._require_session(
            session_id
        )

        return list(session.topics_covered)

    # =========================================================
    # EVALUATIONS
    # =========================================================

    def add_evaluation(
        self,
        session_id: str,
        evaluation: dict[str, Any],
    ) -> None:
        """
        Store one structured answer evaluation.
        """

        session = self._require_session(
            session_id
        )

        session.evaluations.append(
            evaluation
        )

    def get_evaluations(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """
        Return all answer evaluations.
        """

        session = self._require_session(
            session_id
        )

        return list(session.evaluations)

    # =========================================================
    # STRENGTHS
    # =========================================================

    def add_strength(
        self,
        session_id: str,
        strength: str,
    ) -> None:
        """
        Add a candidate strength.

        Duplicate strengths are ignored.
        """

        session = self._require_session(
            session_id
        )

        strength = strength.strip()

        if not strength:
            return

        if strength not in session.strengths:
            session.strengths.append(
                strength
            )

    def get_strengths(
        self,
        session_id: str,
    ) -> list[str]:
        """
        Return all identified candidate strengths.
        """

        session = self._require_session(
            session_id
        )

        return list(session.strengths)

    # =========================================================
    # KNOWLEDGE GAPS
    # =========================================================

    def add_gap(
        self,
        session_id: str,
        gap: str,
    ) -> None:
        """
        Add a candidate knowledge gap.

        Duplicate gaps are ignored.
        """

        session = self._require_session(
            session_id
        )

        gap = gap.strip()

        if not gap:
            return

        if gap not in session.gaps:
            session.gaps.append(
                gap
            )

    def get_gaps(
        self,
        session_id: str,
    ) -> list[str]:
        """
        Return all identified knowledge gaps.
        """

        session = self._require_session(
            session_id
        )

        return list(session.gaps)

    # =========================================================
    # COMPLETION
    # =========================================================

    def mark_completed(
        self,
        session_id: str,
    ) -> None:
        """
        Mark the interview as completed.
        """

        session = self._require_session(
            session_id
        )

        session.completed = True

    def is_completed(
        self,
        session_id: str,
    ) -> bool:
        """
        Return whether the interview is completed.
        """

        session = self._require_session(
            session_id
        )

        return session.completed

    # =========================================================
    # COMPLETE STATE
    # =========================================================

    def get_session_state(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """
        Return a JSON-friendly snapshot of the entire session.

        Useful for debugging and API responses.
        """

        session = self._require_session(
            session_id
        )

        return {
            "sessionId": session.session_id,
            "candidate": session.candidate,
            "conversation": list(
                session.conversation
            ),
            "currentQuestion": session.current_question,
            "currentTopic": session.current_topic,
            "questionCount": session.question_count,
            "topicsCovered": list(
                session.topics_covered
            ),
            "evaluations": list(
                session.evaluations
            ),
            "strengths": list(
                session.strengths
            ),
            "gaps": list(
                session.gaps
            ),
            "completed": session.completed,
        }

    # =========================================================
    # INTERNAL HELPER
    # =========================================================

    def _require_session(
        self,
        session_id: str,
    ) -> InterviewSession:
        """
        Retrieve a session or raise a useful error.
        """

        session = self._sessions.get(
            session_id
        )

        if session is None:
            raise ValueError(
                f"Interview session '{session_id}' does not exist."
            )

        return session