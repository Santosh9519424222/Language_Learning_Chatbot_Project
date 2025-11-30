"""
Translator Agent
Translates PDF content to target languages

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import TRANSLATOR_AGENT_PROMPT
from config.gemini_config import GeminiClient

logger = logging.getLogger(__name__)


class TranslatorAgent(BaseAgent):
    """
    Agent responsible for translating PDF content to target languages.
    Preserves educational value and adds pronunciation guides.
    """

    SUPPORTED_LANGUAGES = [
        'English', 'French', 'Spanish', 'German', 'Italian',
        'Chinese', 'Japanese', 'Korean', 'Hindi', 'Portuguese', 'Arabic'
    ]

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Translator Agent.

        Args:
            gemini_client: Gemini API client instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="TranslatorAgent",
            system_prompt=TRANSLATOR_AGENT_PROMPT,
            temperature=0.5  # Balance accuracy and naturalness
        )

    def process(
        self,
        content: str,
        topics: List[Dict[str, Any]],
        source_language: str,
        target_language: str,
        include_pronunciation: bool = True
    ) -> AgentResponse:
        """
        Translate content and topics to target language.

        Args:
            content: Content to translate
            topics: Topics to translate
            source_language: Source language
            target_language: Target language
            include_pronunciation: Whether to include pronunciation guides

        Returns:
            AgentResponse: Translated content
        """
        start_time = time.time()

        try:
            self.logger.info(f"Translating from {source_language} to {target_language}")

            # Validate target language
            if target_language not in self.SUPPORTED_LANGUAGES:
                return AgentResponse(
                    success=False,
                    error=f"Unsupported target language: {target_language}",
                    agent_name=self.agent_name,
                    duration=time.time() - start_time
                )

            # Translate topics
            translated_topics = self._translate_topics(
                topics=topics,
                target_language=target_language,
                include_pronunciation=include_pronunciation
            )

            # Translate main content (sample)
            translated_content = self._translate_text(
                text=content[:2000],  # Limit for demo
                target_language=target_language
            )

            result_data = {
                'source_language': source_language,
                'target_language': target_language,
                'translated_topics': translated_topics,
                'translated_content': translated_content,
                'include_pronunciation': include_pronunciation,
                'translation_timestamp': time.time()
            }

            duration = time.time() - start_time
            self.log_performance('translation', duration, True)

            self.logger.info(
                f"Translation completed",
                extra={
                    'source': source_language,
                    'target': target_language,
                    'topics': len(translated_topics),
                    'duration': duration
                }
            )

            return AgentResponse(
                success=True,
                data=result_data,
                agent_name=self.agent_name,
                duration=duration
            )

        except Exception as e:
            self.logger.error(f"Translation failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def _translate_topics(
        self,
        topics: List[Dict[str, Any]],
        target_language: str,
        include_pronunciation: bool
    ) -> List[Dict[str, Any]]:
        """Translate list of topics"""
        translated = []

        for topic in topics[:10]:  # Limit to first 10 topics
            try:
                translated_topic = self._translate_single_topic(
                    topic=topic,
                    target_language=target_language,
                    include_pronunciation=include_pronunciation
                )
                translated.append(translated_topic)
            except Exception as e:
                self.logger.warning(f"Failed to translate topic: {e}")
                continue

        return translated

    def _translate_single_topic(
        self,
        topic: Dict[str, Any],
        target_language: str,
        include_pronunciation: bool
    ) -> Dict[str, Any]:
        """Translate a single topic"""
        topic_name = topic.get('name', '')
        topic_desc = topic.get('description', '')

        prompt = f"""
Translate this language learning topic to {target_language}:

Topic Name: {topic_name}
Description: {topic_desc}

Provide:
1. Translated topic name
2. Translated description
{"3. Pronunciation guide (if applicable)" if include_pronunciation else ""}

Keep the educational value intact.
"""

        response = self.generate_response(prompt)
        translation_data = self.parse_json_response(response)

        return {
            'original_name': topic_name,
            'translated_name': translation_data.get('translated_name', topic_name),
            'original_description': topic_desc,
            'translated_description': translation_data.get('translated_description', topic_desc),
            'pronunciation': translation_data.get('pronunciation_guide', '') if include_pronunciation else None
        }

    def _translate_text(self, text: str, target_language: str) -> str:
        """Translate general text"""
        prompt = f"""
Translate this text to {target_language}. Preserve the educational context.

Text: {text}
"""

        try:
            translated = self.generate_response(prompt, temperature=0.4)
            return translated
        except Exception as e:
            self.logger.error(f"Text translation failed: {e}")
            return text

    def translate_text(self, text: str, target_language: str) -> str:
        """Public method to translate text"""
        return self._translate_text(text, target_language)

    def add_pronunciation_hints(self, text: str, language: str) -> str:
        """Add pronunciation hints to text"""
        prompt = f"""
Add pronunciation hints to this {language} text for language learners.

Text: {text}

Format: word (pronunciation)
"""

        try:
            result = self.generate_response(prompt)
            return result
        except Exception as e:
            self.logger.warning(f"Pronunciation hints failed: {e}")
            return text

