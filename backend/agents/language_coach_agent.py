"""
Language Coach Agent
Provides language learning feedback

Author: Santosh Yadav
Date: November 2025
"""

import logging
from .base_agent import LLMAgent, AgentResponse

logger = logging.getLogger(__name__)


class LanguageCoachAgent(LLMAgent):
    """
    Agent for providing language learning feedback.
    """

    def __init__(self, gemini_client, model: str = "gemini-pro"):
        super().__init__(gemini_client, name="language_coach", model=model)

    def process(self, **kwargs) -> AgentResponse:
        """Provide language learning feedback."""
        try:
            user_output = kwargs.get('user_output', '')
            language = kwargs.get('language', 'en')

            if not user_output:
                return self._create_response(success=False, error="Missing user output")

            prompt = f"""Review this {language} language output and provide feedback:

{user_output}

Identify any grammar, vocabulary, or fluency issues. Be encouraging."""

            success, response = self.generate_text(prompt, temperature=0.5, max_tokens=500)

            if success:
                return self._create_response(
                    success=True,
                    data={
                        'feedback': response,
                        'grammar_feedback': 'No major issues',
                        'vocabulary_suggestions': [],
                        'encouragement': 'Great effort!'
                    }
                )

            return self._create_response(success=False, error="Feedback generation failed")
        except Exception as e:
            return self._create_response(success=False, error=str(e))

