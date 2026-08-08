from typing import Any


class InterviewPlanner:
    """
    Plans a personalized technical interview using the
    official cohort curriculum and candidate profile.

    The candidate profile is expected to contain:
        - member
        - missions
        - signals

    Each mission may contain:
        - day
        - title
        - passed
        - skipped
        - attempts
    """

    def __init__(self, curriculum: dict[str, Any]) -> None:
        self.curriculum = curriculum

    # =========================================================
    # CURRICULUM
    # =========================================================

    def get_curriculum_topics(self) -> list[dict[str, Any]]:
        """
        Return the detailed curriculum days.

        The official curriculum stores detailed day information
        inside the top-level 'days' array.
        """

        topics: list[dict[str, Any]] = []

        for day in self.curriculum.get("days", []):
            topics.append(
                {
                    "day": day.get("day"),
                    "title": day.get("title", ""),
                    "type": day.get("type", ""),
                    "tools": day.get("tools", []),
                    "objectives": day.get("objectives", []),
                }
            )

        return topics

    # =========================================================
    # CANDIDATE PROFILE
    # =========================================================

    def get_candidate_missions(
        self,
        candidate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Return the candidate's mission history.
        """

        missions = candidate.get("missions", [])

        if not isinstance(missions, list):
            return []

        return missions

    def get_candidate_signals(
        self,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return the candidate's learning signals.
        """

        signals = candidate.get("signals", {})

        if not isinstance(signals, dict):
            return {}

        return signals

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(value: str) -> str:
        """
        Normalize text so that topic comparisons are
        case-insensitive and whitespace-independent.
        """

        return value.strip().lower()

    # =========================================================
    # MATCHING
    # =========================================================

    def _mission_matches_topic(
        self,
        mission: dict[str, Any],
        topic: dict[str, Any],
    ) -> bool:
        """
        Determine whether a candidate mission corresponds
        to a curriculum day.

        Day number is the strongest signal. Title matching
        is used as a fallback.
        """

        mission_day = mission.get("day")
        curriculum_day = topic.get("day")

        # Prefer exact day matching.
        if (
            mission_day is not None
            and curriculum_day is not None
            and mission_day == curriculum_day
        ):
            return True

        mission_title = self._normalize(
            str(mission.get("title", ""))
        )

        curriculum_title = self._normalize(
            str(topic.get("title", ""))
        )

        if not mission_title or not curriculum_title:
            return False

        if mission_title == curriculum_title:
            return True

        if mission_title in curriculum_title:
            return True

        if curriculum_title in mission_title:
            return True

        return False

    # =========================================================
    # TOPIC STATUS
    # =========================================================

    def get_topic_status(
        self,
        topic: dict[str, Any],
        candidate: dict[str, Any],
    ) -> str:
        """
        Determine the candidate's status for a curriculum topic.

        Possible statuses:

            failed
            skipped
            completed
            attempted
            unseen

        Priority is based on the candidate's actual mission
        history.
        """

        missions = self.get_candidate_missions(candidate)

        matching_missions = [
            mission
            for mission in missions
            if self._mission_matches_topic(mission, topic)
        ]

        if not matching_missions:
            return "unseen"

        # -----------------------------------------------------
        # Failed
        # -----------------------------------------------------

        for mission in matching_missions:
            if mission.get("passed") is False:
                return "failed"

        # -----------------------------------------------------
        # Skipped
        # -----------------------------------------------------

        for mission in matching_missions:
            if mission.get("skipped") is True:
                return "skipped"

        # -----------------------------------------------------
        # Completed
        # -----------------------------------------------------

        for mission in matching_missions:
            if mission.get("passed") is True:
                return "completed"

        # -----------------------------------------------------
        # Attempted
        # -----------------------------------------------------

        for mission in matching_missions:
            attempts = mission.get("attempts", 0)

            if isinstance(attempts, int) and attempts > 0:
                return "attempted"

        return "unseen"

    # =========================================================
    # CANDIDATE + CURRICULUM MAP
    # =========================================================

    def get_candidate_topic_details(
        self,
        candidate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Combine the official curriculum with the candidate's
        mission history.

        Example result:

        {
            "day": 8,
            "title": "Vector Databases Overview",
            "status": "completed",
            ...
        }
        """

        details: list[dict[str, Any]] = []

        for topic in self.get_curriculum_topics():

            status = self.get_topic_status(
                topic,
                candidate,
            )

            details.append(
                {
                    **topic,
                    "status": status,
                }
            )

        return details

    # =========================================================
    # INTERVIEW TOPIC SELECTION
    # =========================================================

    def choose_next_topic(
        self,
        candidate: dict[str, Any],
        covered_topics: list[str],
    ) -> dict[str, Any] | None:
        """
        Choose the next primary interview topic.

        Priority:

        1. Failed topics
        2. Attempted topics
        3. Completed topics
        4. Unseen topics

        Skipped topics are avoided.

        Topics already covered during this interview
        are also avoided.
        """

        topic_details = self.get_candidate_topic_details(
            candidate
        )

        covered = {
            self._normalize(topic)
            for topic in covered_topics
        }

        # -----------------------------------------------------
        # Priority 1: Failed topics
        # -----------------------------------------------------

        for topic in topic_details:

            if topic["status"] != "failed":
                continue

            if self._normalize(topic["title"]) in covered:
                continue

            return topic

        # -----------------------------------------------------
        # Priority 2: Attempted topics
        # -----------------------------------------------------

        for topic in topic_details:

            if topic["status"] != "attempted":
                continue

            if self._normalize(topic["title"]) in covered:
                continue

            return topic

        # -----------------------------------------------------
        # Priority 3: Completed topics
        # -----------------------------------------------------

        for topic in topic_details:

            if topic["status"] != "completed":
                continue

            if self._normalize(topic["title"]) in covered:
                continue

            return topic

        # -----------------------------------------------------
        # Priority 4: Unseen topics
        # -----------------------------------------------------

        for topic in topic_details:

            if topic["status"] != "unseen":
                continue

            if self._normalize(topic["title"]) in covered:
                continue

            return topic

        # -----------------------------------------------------
        # No eligible topic
        # -----------------------------------------------------

        return None

    # =========================================================
    # LOOKUP BY DAY
    # =========================================================

    def get_topic_by_day(
        self,
        day_number: int,
    ) -> dict[str, Any] | None:
        """
        Find a curriculum topic by its day number.
        """

        for topic in self.get_curriculum_topics():

            if topic.get("day") == day_number:
                return topic

        return None

    # =========================================================
    # LOOKUP BY TITLE
    # =========================================================

    def get_topic_by_title(
        self,
        title: str,
    ) -> dict[str, Any] | None:
        """
        Find a curriculum topic by title.
        """

        normalized_title = self._normalize(title)

        for topic in self.get_curriculum_topics():

            topic_title = self._normalize(
                topic.get("title", "")
            )

            if topic_title == normalized_title:
                return topic

        return None

    # =========================================================
    # CANDIDATE INFORMATION
    # =========================================================

    def get_candidate_profile(
        self,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Return useful candidate information for the interviewer.
        """

        member = candidate.get("member", {})

        if not isinstance(member, dict):
            member = {}

        return {
            "id": member.get("id"),
            "name": member.get("name"),
            "jobRole": member.get("jobRole"),
            "yearsExperience": member.get("yearsExperience"),
            "education": member.get("education"),
            "status": member.get("status"),
        }