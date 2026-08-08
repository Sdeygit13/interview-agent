import json
from typing import Any

from openai import OpenAI

from backend.config import GEMINI_API_KEY, GEMINI_MODEL


class LLMService:
    """
    Centralized service for communicating with Gemini.

    Gemini is accessed through Google's OpenAI-compatible
    API endpoint, allowing the rest of the application to
    continue using the existing OpenAI Python SDK interface.
    """

    def __init__(self) -> None:

        self.client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=(
                "https://generativelanguage.googleapis.com/"
                "v1beta/openai/"
            ),
        )

        self.model = GEMINI_MODEL

    # ========================================================
    # BASIC GENERATION
    # ========================================================

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a text response from Gemini.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return content.strip()

    # ========================================================
    # GENERATION WITH HISTORY
    # ========================================================

    def generate_with_history(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a response using the complete conversation
        history.

        This allows the interviewer to maintain context across
        multiple interview turns.
        """

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        messages.extend(conversation)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=messages,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return content.strip()

    # ========================================================
    # JSON GENERATION
    # ========================================================

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """
        Generate a machine-readable JSON object.

        This is used by the evaluator and feedback system.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={
                "type": "json_object"
            },
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Gemini returned an empty JSON response."
            )

        try:
            result = json.loads(content)

        except json.JSONDecodeError as exc:

            raise RuntimeError(
                "Gemini returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):

            raise RuntimeError(
                "Gemini JSON response must be an object."
            )

        return result


# ============================================================
# SHARED SERVICE INSTANCE
# ============================================================

llm_service = LLMService()