"""
Context Guard Agent
Validates question relevance and prevents off-topic queries

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import CONTEXT_GUARD_AGENT_PROMPT
from config.gemini_config import GeminiClient

logger = logging.getLogger(__name__)


class ContextGuardAgent(BaseAgent):
    """
    Agent responsible for validating question relevance to PDF content.
    Prevents off-topic queries and prompt injection attacks.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Context Guard Agent.

        Args:
            gemini_client: Gemini API client instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="ContextGuardAgent",
            system_prompt=CONTEXT_GUARD_AGENT_PROMPT,
            temperature=0.3  # Lower temp for consistent validation
        )

    def process(self, topics: List[Dict[str, Any]], user_query: str) -> AgentResponse:
        """
        Validate if user's question is relevant to PDF content.

        Args:
            topics: List of topics extracted from PDF
            user_query: User's question

        Returns:
            AgentResponse: Validation result with relevance score
        """
        start_time = time.time()

        try:
            self.logger.info(f"Validating query relevance: '{user_query[:50]}...'")

            # Step 1: Check for obvious prompt injection attempts
            if self._detect_prompt_injection(user_query):
                return AgentResponse(
                    success=True,
                    data={
                        'is_relevant': False,
                        'relevance_score': 0.0,
                        'reason': 'Potential prompt injection detected',
                        'allow_query': False,
                        'user_message': 'Your question contains invalid content. Please ask about the PDF material.'
                    },
                    agent_name=self.agent_name,
                    duration=time.time() - start_time
                )

            # Step 2: Quick keyword check
            quick_check = self._quick_relevance_check(topics, user_query)

            # Step 3: If quick check fails, use AI for deeper analysis
            if not quick_check['is_relevant']:
                ai_check = self._ai_relevance_check(topics, user_query)

                duration = time.time() - start_time
                self.log_performance('context_validation', duration, True)

                return AgentResponse(
                    success=True,
                    data=ai_check,
                    agent_name=self.agent_name,
                    duration=duration
                )

            # Quick check passed
            duration = time.time() - start_time
            self.log_performance('context_validation', duration, True)

            return AgentResponse(
                success=True,
                data=quick_check,
                agent_name=self.agent_name,
                duration=duration
            )

        except Exception as e:
            self.logger.error(f"Context validation failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def _detect_prompt_injection(self, query: str) -> bool:
        """
        Detect potential prompt injection attempts.

        Args:
            query: User query

        Returns:
            bool: True if injection detected
        """
        injection_patterns = [
            'ignore previous instructions',
            'ignore all previous',
            'disregard previous',
            'forget previous',
            'new instructions',
            'system prompt',
            'you are now',
            'act as',
            'pretend to be',
            'roleplay as'
        ]

        query_lower = query.lower()

        for pattern in injection_patterns:
            if pattern in query_lower:
                self.logger.warning(f"Prompt injection detected: {pattern}")
                return True

        return False

    def _quick_relevance_check(self, topics: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Quick keyword-based relevance check.

        Args:
            topics: List of topics
            query: User query

        Returns:
            dict: Quick validation result
        """
        query_lower = query.lower()

        # Extract keywords from topics
        topic_keywords = []
        for topic in topics:
            if isinstance(topic, dict):
                topic_name = topic.get('name', '').lower()
                topic_desc = topic.get('description', '').lower()
                topic_keywords.extend(topic_name.split())
                topic_keywords.extend(topic_desc.split())

        # Check for keyword overlap
        query_words = set(query_lower.split())
        topic_word_set = set(topic_keywords)

        overlap = query_words.intersection(topic_word_set)
        overlap_score = len(overlap) / max(len(query_words), 1)

        if overlap_score > 0.2:  # 20% word overlap
            return {
                'is_relevant': True,
                'relevance_score': min(overlap_score * 2, 1.0),
                'reason': 'Query contains relevant keywords',
                'related_topics': [t.get('name', '') for t in topics if isinstance(t, dict)][:3],
                'allow_query': True,
                'user_message': ''
            }

        return {
            'is_relevant': False,
            'relevance_score': overlap_score,
            'reason': 'No significant keyword overlap detected',
            'related_topics': [],
            'allow_query': False,
            'user_message': ''
        }

    def _ai_relevance_check(self, topics: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Use AI for deep relevance analysis.

        Args:
            topics: List of topics
            query: User query

        Returns:
            dict: AI validation result
        """
        # Format topics for AI
        topics_str = "\n".join([
            f"- {t.get('name', 'Unknown')}: {t.get('description', '')[:100]}"
            for t in topics[:10] if isinstance(t, dict)
        ])

        prompt = f"""
PDF Topics:
{topics_str}

User Question: {query}

Is this question relevant to the PDF content? Should it be allowed?
"""

        try:
            response = self.generate_response(prompt)
            result = self.parse_json_response(response)

            # Ensure required fields
            if 'is_relevant' not in result:
                result['is_relevant'] = False
            if 'allow_query' not in result:
                result['allow_query'] = result.get('is_relevant', False)

            return result

        except Exception as e:
            self.logger.error(f"AI relevance check failed: {e}")
            # Default to allowing query on error (fail open)
            return {
                'is_relevant': True,
                'relevance_score': 0.5,
                'reason': 'Could not validate relevance',
                'related_topics': [],
                'allow_query': True,
                'user_message': ''
            }

    def is_query_relevant(self, topics: List[Dict[str, Any]], query: str) -> bool:
        """
        Simple boolean check for query relevance.

        Args:
            topics: List of topics
            query: User query

        Returns:
            bool: True if relevant
        """
        result = self.process(topics, query)
        if result.success:
            return result.data.get('allow_query', False)
        return False

    def find_related_topics(self, topics: List[Dict[str, Any]], query: str) -> List[str]:
        """
        Find topics related to the query.

        Args:
            topics: List of topics
            query: User query

        Returns:
            List[str]: Related topic names
        """
        result = self.process(topics, query)
        if result.success:
            return result.data.get('related_topics', [])
        return []

