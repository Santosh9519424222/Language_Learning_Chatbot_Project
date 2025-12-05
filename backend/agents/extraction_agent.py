"""
Extraction Agent
Extracts topics, vocabulary, and grammar points from PDFs

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import List, Dict, Any, Optional
from .base_agent import LLMAgent, StorageAgent, AgentResponse

logger = logging.getLogger(__name__)


class ExtractionAgent(LLMAgent, StorageAgent):
    """
    Agent for extracting educational content from PDFs.

    Responsibilities:
    - Extract topics and subtopics
    - Identify key vocabulary
    - Extract grammar points
    - Determine difficulty levels
    - Create vector embeddings
    """

    def __init__(self, gemini_client, vector_store=None, model: str = "gemini-pro"):
        """
        Initialize Extraction Agent.

        Args:
            gemini_client: Initialized GeminiClient
            vector_store: Optional ChromaVectorStore
            model: LLM model to use
        """
        LLMAgent.__init__(self, gemini_client, name="extraction", model=model)
        self.vector_store = vector_store

    def process(
        self,
        file_path: str,
        pdf_id: str,
        language: str = "en"
    ) -> AgentResponse:
        """
        Extract educational content from PDF.

        Args:
            file_path: Path to PDF file
            pdf_id: PDF identifier
            language: Document language (ISO 639-1)

        Returns:
            AgentResponse with extracted topics and vocabulary
        """
        start_time = time.time()

        try:
            from storage.pdf_handler import extract_text_from_pdf, extract_text_chunks

            # Extract full text
            extraction_result = extract_text_from_pdf(file_path)
            full_text = extraction_result.get('full_text', '')
            text_by_page = extraction_result.get('text_by_page', {})

            if not full_text:
                return self._create_response(
                    success=False,
                    error="No text could be extracted from PDF",
                    execution_time=time.time() - start_time
                )

            # Extract topics
            topics = self._extract_topics(full_text, language)

            # Extract vocabulary
            vocabulary = self._extract_vocabulary(full_text, language)

            # Extract grammar points (if language learning focused)
            grammar_points = self._extract_grammar_points(full_text, language) if language != "en" else []

            # Create chunks for vector store
            chunks = extract_text_chunks(file_path, chunk_size=1000, overlap=200)

            # Index chunks in vector store if available
            if self.vector_store and chunks:
                try:
                    self.vector_store.add_pdf_chunks(pdf_id, chunks)
                    logger.info(f"Indexed {len(chunks)} chunks for PDF {pdf_id}")
                except Exception as e:
                    logger.warning(f"Failed to index chunks in vector store: {str(e)}")

            response_data = {
                'topics': topics,
                'key_vocabulary': vocabulary,
                'grammar_points': grammar_points,
                'chunks_indexed': len(chunks),
                'text_length': len(full_text),
                'pages_processed': len(text_by_page)
            }

            execution_time = time.time() - start_time
            return self._create_response(
                success=True,
                data=response_data,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Content extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._create_response(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )

    def _extract_topics(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Extract main topics from text using AI.

        Args:
            text: Document text
            language: Document language

        Returns:
            List of topic dictionaries
        """
        try:
            prompt = f"""Extract the main topics from this educational text. For each topic, provide:
- name: Topic title
- description: Brief explanation (1-2 sentences)
- difficulty: Beginner/Intermediate/Advanced
- key_vocabulary: Important terms (comma-separated)

Text:
{text[:3000]}

Return as JSON array:
[{{"name": "...", "description": "...", "difficulty": "...", "key_vocabulary": "..."}}]"""

            success, response = self.generate_text(prompt, temperature=0.5, max_tokens=1000)

            if success:
                success, parsed = self.parse_json_response(response)
                if success and isinstance(parsed, list):
                    return parsed[:10]  # Limit to 10 topics

            # Fallback
            return [{"name": "Document Content", "description": "Main topic", "difficulty": "Intermediate", "key_vocabulary": ""}]

        except Exception as e:
            logger.warning(f"Topic extraction failed: {str(e)}, using default")
            return [{"name": "Document Content", "description": "Main topic", "difficulty": "Intermediate", "key_vocabulary": ""}]

    def _extract_vocabulary(self, text: str, language: str = "en") -> List[Dict[str, str]]:
        """
        Extract key vocabulary from text.

        Args:
            text: Document text
            language: Document language

        Returns:
            List of vocabulary items with definitions
        """
        try:
            prompt = f"""Extract 10-15 key vocabulary terms from this text. For each term:
- word: The term
- definition: Definition in simple terms
- difficulty: Beginner/Intermediate/Advanced

Text:
{text[:2000]}

Return as JSON array:
[{{"word": "...", "definition": "...", "difficulty": "..."}}]"""

            success, response = self.generate_text(prompt, temperature=0.3, max_tokens=800)

            if success:
                success, parsed = self.parse_json_response(response)
                if success and isinstance(parsed, list):
                    return parsed[:15]

            return []

        except Exception as e:
            logger.warning(f"Vocabulary extraction failed: {str(e)}")
            return []

    def _extract_grammar_points(self, text: str, language: str = "en") -> List[str]:
        """
        Extract grammar points relevant to language learning.

        Args:
            text: Document text
            language: Document language

        Returns:
            List of grammar points
        """
        try:
            if language == "en":
                return []

            prompt = f"""Identify 5-8 important grammar patterns or rules from this {language} text.

Text:
{text[:2000]}

Return as JSON array of strings:
["grammar point 1", "grammar point 2", ...]"""

            success, response = self.generate_text(prompt, temperature=0.3, max_tokens=500)

            if success:
                success, parsed = self.parse_json_response(response)
                if success and isinstance(parsed, list):
                    return parsed[:8]

            return []

        except Exception as e:
            logger.warning(f"Grammar extraction failed: {str(e)}")
            return []

