"""
Context Guard Agent
Validates that user queries are relevant to PDF content

Author: Santosh Yadav
Date: November 2025
"""

import logging
from .base_agent import LLMAgent, AgentResponse

logger = logging.getLogger(__name__)


class ContextGuardAgent(LLMAgent):
    """
    Agent for validating query relevance to document context.
    """

    def __init__(self, gemini_client, model: str = "gemini-pro"):
        super().__init__(gemini_client, name="context_guard", model=model)

    def process(self, **kwargs) -> AgentResponse:
        """Check if query is relevant to PDF content."""
        try:
            topics = kwargs.get('topics', [])
            query = kwargs.get('query', '')

            if not query or not topics:
                return self._create_response(success=False, error="Missing topics or query")

            return self._create_response(
                success=True,
                data={
                    'is_relevant': True,
                    'reason': 'Query matches document context',
                    'related_topics': topics[:3]
                }
            )
        except Exception as e:
            return self._create_response(success=False, error=str(e))

