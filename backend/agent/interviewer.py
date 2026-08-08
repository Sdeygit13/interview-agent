from typing import Any

from backend.agent.evaluator import AnswerEvaluator
from backend.agent.planner import InterviewPlanner
from backend.services.llm import LLMService
from backend.services.session import InterviewSession, SessionManager


# ============================================================
# HACKATHON REQUIREMENTS
# ============================================================

MIN_QUESTIONS = 8
MIN_DAYS = 4

# Maximum number of consecutive follow-up questions
# allowed on the same curriculum topic.
MAX_FOLLOWUPS_PER_TOPIC = 2


class Interviewer:
    """
    Core conversational AI interviewer.

    Responsibilities:
        - Start interviews
        - Select curriculum topics
        - Generate technical questions
        - Process candidate answers
        - Evaluate answers
        - Generate adaptive follow-ups
        - Guarantee curriculum coverage
        - Track interview progress
        - Complete the interview after requirements are met
    """

    def __init__(
        self,
        planner: InterviewPlanner,
        llm: LLMService,
        evaluator: AnswerEvaluator,
        sessions: SessionManager,
    ) -> None:

        self.planner = planner
        self.llm = llm
        self.evaluator = evaluator
        self.sessions = sessions

        # Runtime tracking of consecutive follow-ups.
        #
        # Example:
        #
        # session_id -> {
        #     "topic": "Vector Databases Overview",
        #     "count": 2
        # }
        #
        self._follow_up_state: dict[str, dict[str, Any]] = {}

    # =========================================================
    # SYSTEM PROMPT
    # =========================================================

    def _build_system_prompt(
        self,
        candidate: dict[str, Any],
    ) -> str:

        member = candidate.get("member", {})

        name = member.get(
            "name",
            "Candidate",
        )

        role = member.get(
            "jobRole",
            "Technical Candidate",
        )

        experience = member.get(
            "yearsExperience",
            "unknown",
        )

        education = member.get(
            "education",
            "unknown",
        )

        return f"""
You are an experienced senior technical interviewer
conducting a realistic AI engineering interview.

Candidate:
- Name: {name}
- Role: {role}
- Experience: {experience} years
- Education: {education}

Your task is to conduct a personalized, conversational,
multi-turn technical interview based on the candidate's
learning journey and the supplied AI cohort curriculum.

Interview behavior:

1. Ask exactly ONE question at a time.

2. Adapt questions to the candidate's previous answers.

3. Probe:
   - technical understanding
   - reasoning
   - implementation knowledge
   - architecture
   - trade-offs
   - practical engineering judgment

4. Prefer reasoning over memorized definitions.

5. Keep questions concise and natural.

6. Do not reveal internal evaluation or scoring.

7. Do not provide the answer to the candidate.

8. Stay strictly within the supplied curriculum.

9. Follow-up questions should investigate a genuine
   weakness, ambiguity, or deeper technical implication.

10. Do not repeatedly ask questions about the same narrow
    sub-topic when the candidate has demonstrated enough
    understanding.

11. When instructed to move to a NEW curriculum topic,
    completely switch to that topic.

12. Never ask multiple unrelated questions in one turn.

The interview must feel like a real senior technical
interview, not a scripted quiz.
""".strip()

    # =========================================================
    # TOPIC CONTEXT
    # =========================================================

    def _build_topic_context(
        self,
        topic: dict[str, Any],
    ) -> str:

        objectives = topic.get(
            "objectives",
            [],
        )

        tools = topic.get(
            "tools",
            [],
        )

        objectives_text = "\n".join(
            f"- {objective}"
            for objective in objectives
        )

        tools_text = ", ".join(
            str(tool)
            for tool in tools
        )

        return f"""
Curriculum day: {topic.get("day")}
Topic: {topic.get("title")}
Type: {topic.get("type")}

Tools:
{tools_text}

Learning objectives:
{objectives_text}
""".strip()

    # =========================================================
    # START INTERVIEW
    # =========================================================

    def start_interview(
        self,
        session_id: str,
        candidate: dict[str, Any],
    ) -> str:

        existing_session = self.sessions.get_session(
            session_id
        )

        if existing_session is not None:
            return (
                existing_session.current_question
                or "The interview session already exists."
            )

        session = self.sessions.create_session(
            session_id=session_id,
            candidate=candidate,
        )

        # Reset follow-up state.
        self._follow_up_state[session_id] = {
            "topic": None,
            "count": 0,
        }

        topic = self.planner.choose_next_topic(
            candidate=candidate,
            covered_topics=session.topics_covered,
        )

        if topic is None:
            raise RuntimeError(
                "No suitable curriculum topic was found "
                "for this candidate."
            )

        question = self._generate_question(
            session=session,
            topic=topic,
            is_follow_up=False,
        )

        self._record_question(
            session=session,
            question=question,
            topic=topic,
        )

        return question

    # =========================================================
    # PROCESS ANSWER
    # =========================================================

    def process_answer(
        self,
        session_id: str,
        answer: str,
    ) -> str:

        session = self.sessions.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                f"Interview session '{session_id}' "
                "does not exist."
            )

        if session.completed:
            return (
                "This interview has already been completed. "
                "Please review your feedback."
            )

        answer = answer.strip()

        if not answer:
            return (
                "Please provide your answer before "
                "we continue."
            )

        # -----------------------------------------------------
        # 1. Store candidate answer
        # -----------------------------------------------------

        self.sessions.add_message(
            session_id=session_id,
            role="user",
            content=answer,
        )

        # -----------------------------------------------------
        # 2. Evaluate candidate answer
        # -----------------------------------------------------

        evaluation = self.evaluator.evaluate(
            session_id=session_id,
            answer=answer,
        )

        # -----------------------------------------------------
        # 3. Determine whether we MUST switch topics
        # -----------------------------------------------------

        current_topic = self._get_current_topic(
            session
        )

        if current_topic is None:
            raise RuntimeError(
                "Unable to determine the current "
                "curriculum topic."
            )

        current_topic_title = current_topic.get(
            "title",
            "",
        )

        follow_up_state = self._follow_up_state.get(
            session_id,
            {
                "topic": current_topic_title,
                "count": 0,
            },
        )

        # If the topic changed somehow, reset the counter.
        if (
            follow_up_state.get("topic")
            != current_topic_title
        ):
            follow_up_state = {
                "topic": current_topic_title,
                "count": 0,
            }

        consecutive_followups = int(
            follow_up_state.get(
                "count",
                0,
            )
        )

        # -----------------------------------------------------
        # 4. Check whether curriculum coverage is still below
        #    the required minimum.
        # -----------------------------------------------------

        topics_covered_count = len(
            session.topics_covered
        )

        questions_asked = session.question_count

        coverage_incomplete = (
            topics_covered_count < MIN_DAYS
        )

        # -----------------------------------------------------
        # 5. Decide whether follow-up is allowed
        # -----------------------------------------------------

        evaluator_wants_followup = (
            self.evaluator.should_follow_up(
                evaluation
            )
        )

        followup_allowed = (
            evaluator_wants_followup
            and consecutive_followups
            < MAX_FOLLOWUPS_PER_TOPIC
        )

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # If we still need curriculum coverage, do NOT allow
        # the LLM to endlessly continue the same topic.
        #
        # Once we have enough depth, force a new topic.
        # -----------------------------------------------------

        if coverage_incomplete:

            # Allow at most one follow-up before moving on.
            if consecutive_followups >= 1:
                followup_allowed = False

        # -----------------------------------------------------
        # 6. Completion check
        #
        # Only complete AFTER the answer has been evaluated.
        # -----------------------------------------------------

        if self.is_ready_for_completion(
            session_id=session_id,
        ):

            self.sessions.mark_completed(
                session_id=session_id,
            )

            self._follow_up_state.pop(
                session_id,
                None,
            )

            return (
                "Thank you. That completes the technical "
                "interview. Your feedback is now being prepared."
            )

        # -----------------------------------------------------
        # 7A. FOLLOW-UP
        # -----------------------------------------------------

        if followup_allowed:

            question = self._generate_question(
                session=session,
                topic=current_topic,
                is_follow_up=True,
                evaluation=evaluation,
            )

            # Increment consecutive follow-up count.
            self._follow_up_state[session_id] = {
                "topic": current_topic_title,
                "count": consecutive_followups + 1,
            }

            self._record_question(
                session=session,
                question=question,
                topic=current_topic,
            )

            return question

        # -----------------------------------------------------
        # 7B. NEW CURRICULUM TOPIC
        # -----------------------------------------------------

        next_topic = self.planner.choose_next_topic(
            candidate=session.candidate,
            covered_topics=session.topics_covered,
        )

        # -----------------------------------------------------
        # If there is no new topic, fall back to current topic.
        # This should normally happen only when the curriculum
        # has been exhausted.
        # -----------------------------------------------------

        if next_topic is None:

            # If requirements are not met, this is a genuine
            # configuration problem rather than something we
            # should silently hide.
            if not self.is_ready_for_completion(
                session_id=session_id,
            ):
                raise RuntimeError(
                    "No additional curriculum topics are "
                    "available, but the minimum interview "
                    "requirements have not been satisfied."
                )

            next_topic = current_topic

        # Reset follow-up counter because we are changing topic.
        self._follow_up_state[session_id] = {
            "topic": next_topic.get(
                "title",
                "",
            ),
            "count": 0,
        }

        question = self._generate_question(
            session=session,
            topic=next_topic,
            is_follow_up=False,
            evaluation=evaluation,
        )

        self._record_question(
            session=session,
            question=question,
            topic=next_topic,
        )

        return question

    # =========================================================
    # GENERATE QUESTION
    # =========================================================

    def _generate_question(
        self,
        session: InterviewSession,
        topic: dict[str, Any],
        is_follow_up: bool,
        evaluation: dict[str, Any] | None = None,
    ) -> str:

        system_prompt = self._build_system_prompt(
            session.candidate
        )

        topic_context = self._build_topic_context(
            topic
        )

        # -----------------------------------------------------
        # FOLLOW-UP INSTRUCTION
        # -----------------------------------------------------

        if is_follow_up:

            follow_up_reason = ""

            if evaluation:
                follow_up_reason = evaluation.get(
                    "followUpReason",
                    "",
                )

            instruction = f"""
This is a FOLLOW-UP question.

The candidate has just answered a question about:

{topic.get("title")}

Reason deeper probing is useful:

{follow_up_reason}

Ask ONE focused technical follow-up question.

The follow-up must:
- directly relate to the candidate's previous answer;
- investigate reasoning or a technical weakness;
- avoid repeating the previous question;
- remain within the current curriculum topic;
- be concise.

Do not reveal evaluation or scoring.
""".strip()

        # -----------------------------------------------------
        # NEW TOPIC INSTRUCTION
        # -----------------------------------------------------

        else:

            instruction = f"""
This is a NEW CURRICULUM TOPIC.

The interview is intentionally moving away from
the previous topic.

Current curriculum topic:

{topic.get("title")}

Curriculum day:

{topic.get("day")}

Ask ONE technical interview question based specifically
on this topic and its learning objectives.

The question should test:
- understanding;
- reasoning;
- implementation;
- architecture;
- trade-offs; or
- practical engineering judgment.

Do NOT continue the previous topic.

Do not ask a basic definition question unless the
curriculum specifically requires foundational knowledge.
""".strip()

        # -----------------------------------------------------
        # EVALUATION CONTEXT
        # -----------------------------------------------------

        evaluation_context = ""

        if evaluation:

            gaps = evaluation.get(
                "gaps",
                [],
            )

            strengths = evaluation.get(
                "strengths",
                [],
            )

            evaluation_context = f"""
Internal evaluation context:

Strengths:
{chr(10).join(f"- {item}" for item in strengths)}

Knowledge gaps:
{chr(10).join(f"- {item}" for item in gaps)}

Use this information internally to make the question
appropriate for the candidate's level.

Never reveal this evaluation information.
""".strip()

        # -----------------------------------------------------
        # USER PROMPT
        # -----------------------------------------------------

        user_prompt = f"""
{topic_context}

{instruction}

{evaluation_context}

The previous conversation is available in the
conversation history.

Return ONLY the interview question.

Do not include:
- scoring
- evaluation
- answer hints
- explanations
- headings
- multiple questions
""".strip()

        conversation = [
            *session.conversation,
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        question = self.llm.generate_with_history(
            system_prompt=system_prompt,
            conversation=conversation,
            temperature=0.7,
        )

        return question.strip()

    # =========================================================
    # RECORD QUESTION
    # =========================================================

    def _record_question(
        self,
        session: InterviewSession,
        question: str,
        topic: dict[str, Any],
    ) -> None:

        self.sessions.add_message(
            session_id=session.session_id,
            role="assistant",
            content=question,
        )

        self.sessions.increment_question_count(
            session_id=session.session_id,
        )

        self.sessions.set_current_question(
            session_id=session.session_id,
            question=question,
            topic=topic.get(
                "title",
                "",
            ),
        )

        self.sessions.add_topic(
            session_id=session.session_id,
            topic=topic.get(
                "title",
                "",
            ),
        )

    # =========================================================
    # CURRENT TOPIC
    # =========================================================

    def _get_current_topic(
        self,
        session: InterviewSession,
    ) -> dict[str, Any] | None:

        if not session.current_topic:
            return None

        return self.planner.get_topic_by_title(
            session.current_topic
        )

    # =========================================================
    # PROGRESS
    # =========================================================

    def get_progress(
        self,
        session_id: str,
    ) -> dict[str, Any]:

        session = self.sessions.get_session(
            session_id
        )

        if session is None:
            raise ValueError(
                f"Interview session '{session_id}' "
                "does not exist."
            )

        follow_up_state = self._follow_up_state.get(
            session_id,
            {},
        )

        return {
            "questionsAsked": session.question_count,
            "topicsCovered": len(
                session.topics_covered
            ),
            "topicNames": session.topics_covered,
            "currentTopic": session.current_topic,
            "consecutiveFollowups": follow_up_state.get(
                "count",
                0,
            ),
            "minimumQuestions": MIN_QUESTIONS,
            "minimumDays": MIN_DAYS,
            "readyForCompletion": self.is_ready_for_completion(
                session_id
            ),
            "completed": session.completed,
        }

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_ready_for_completion(
        self,
        session_id: str,
    ) -> bool:

        session = self.sessions.get_session(
            session_id
        )

        if session is None:
            return False

        return (
            session.question_count >= MIN_QUESTIONS
            and len(session.topics_covered) >= MIN_DAYS
        )