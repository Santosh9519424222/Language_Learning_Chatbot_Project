"""
Translator Agent
Translates content to target languages

Author: Santosh Yadav
Date: November 2025
"""

import logging
from .base_agent import LLMAgent, AgentResponse

logger = logging.getLogger(__name__)


class TranslatorAgent(LLMAgent):
    """
    Agent for translating content between languages.
    """

    def __init__(self, gemini_client, model: str = "gemini-pro"):
        super().__init__(gemini_client, name="translator", model=model)

    def process(self, **kwargs) -> AgentResponse:
        """Translate content to target language."""
        try:
            content = kwargs.get('content', '')
            target_language = kwargs.get('target_language', 'es')

            if not content:
                return self._create_response(success=False, error="Missing content")

            prompt = f"""Translate this text to {target_language}:

{content[:1000]}

Provide only the translation."""

            success, response = self.generate_text(prompt, temperature=0.3, max_tokens=800)

            if success:
                return self._create_response(
                    success=True,
                    data={
                        'original': content[:100],
                        'translated': response,
                        'target_language': target_language
                    }
                )

            return self._create_response(success=False, error="Translation failed")
        except Exception as e:
            return self._create_response(success=False, error=str(e))

