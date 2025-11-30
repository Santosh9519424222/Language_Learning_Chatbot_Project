"""
Extraction Agent
Extracts topics, vocabulary, grammar points from PDF content

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import EXTRACTION_AGENT_PROMPT
from config.gemini_config import GeminiClient
from storage.vector_store import ChromaVectorStore
from storage.pdf_handler import PDFHandler

logger = logging.getLogger(__name__)


class ExtractionAgent(BaseAgent):
    """
    Agent responsible for extracting structured learning content from PDFs.
    Extracts topics, vocabulary, grammar points, and learning objectives.
    """

    def __init__(self, gemini_client: GeminiClient, vector_store: ChromaVectorStore):
        """
        Initialize Extraction Agent.

        Args:
            gemini_client: Gemini API client instance
            vector_store: ChromaDB vector store instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="ExtractionAgent",
            system_prompt=EXTRACTION_AGENT_PROMPT,
            temperature=0.5
        )
        self.vector_store = vector_store
        self.pdf_handler = PDFHandler()

    def process(self, file_path: str, pdf_id: str, language: str) -> AgentResponse:
        """
        Extract topics, vocabulary, and grammar from PDF.

        Args:
            file_path: Path to PDF file
            pdf_id: PDF identifier
            language: Detected language

        Returns:
            AgentResponse: Extracted topics and learning content
        """
        start_time = time.time()

        try:
            self.logger.info(f"Extracting content from PDF: {pdf_id}")

            # Step 1: Extract full text
            extraction_result = self.pdf_handler.extract_text_from_pdf(file_path)
            full_text = extraction_result['full_text']

            # Step 2: Create chunks for vector store
            chunks = self.pdf_handler.extract_text_chunks(file_path)

            # Step 3: Add chunks to vector store
            self.vector_store.add_pdf_chunks(pdf_id, chunks)
            self.logger.info(f"Added {len(chunks)} chunks to vector store")

            # Step 4: Extract topics using AI
            topics = self._extract_topics_with_ai(full_text, language)

            # Step 5: Extract vocabulary
            vocabulary = self._extract_vocabulary(full_text, language)

            # Step 6: Extract grammar points
            grammar_points = self._extract_grammar_points(full_text, language)

            result_data = {
                'pdf_id': pdf_id,
                'topics': topics,
                'total_topics': len(topics),
                'vocabulary': vocabulary,
                'grammar_points': grammar_points,
                'chunks_indexed': len(chunks),
                'language': language,
                'extraction_timestamp': time.time()
            }

            duration = time.time() - start_time
            self.log_performance('content_extraction', duration, True)

            self.logger.info(
                f"Content extraction completed",
                extra={
                    'pdf_id': pdf_id,
                    'topics': len(topics),
                    'vocabulary': len(vocabulary),
                    'chunks': len(chunks),
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
            self.logger.error(f"Content extraction failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def _extract_topics_with_ai(self, text: str, language: str) -> List[Dict[str, Any]]:
        """Extract topics using AI analysis"""
        # Split text into manageable chunks (Gemini has token limits)
        max_chars = 10000
        text_chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

        all_topics = []

        for i, chunk in enumerate(text_chunks[:5]):  # Limit to first 5 chunks
            prompt = f"""
Analyze this section of a {language} learning PDF and extract topics.

Text Section {i+1}:
{chunk}

Extract:
- Main topics and subtopics
- Key vocabulary for each topic
- Grammar points covered
- Difficulty level
"""

            try:
                response = self.generate_response(prompt)
                extracted = self.parse_json_response(response)

                if 'topics' in extracted and isinstance(extracted['topics'], list):
                    all_topics.extend(extracted['topics'])

            except Exception as e:
                self.logger.warning(f"Failed to extract from chunk {i+1}: {e}")
                continue

        return all_topics

    def _extract_vocabulary(self, text: str, language: str) -> List[Dict[str, Any]]:
        """Extract key vocabulary items"""
        # Use AI to identify important vocabulary
        text_sample = text[:5000]  # Use first 5000 chars

        prompt = f"""
From this {language} learning content, extract the 20 most important vocabulary words.

Text:
{text_sample}

For each word provide:
- The word
- Definition
- Example sentence
- Difficulty level
"""

        try:
            response = self.generate_response(prompt)
            extracted = self.parse_json_response(response)

            if 'key_vocabulary' in extracted:
                return extracted['key_vocabulary']
            elif 'vocabulary' in extracted:
                return extracted['vocabulary']
            else:
                return []

        except Exception as e:
            self.logger.warning(f"Vocabulary extraction failed: {e}")
            return []

    def _extract_grammar_points(self, text: str, language: str) -> List[str]:
        """Extract grammar points covered"""
        text_sample = text[:5000]

        prompt = f"""
Identify the main grammar concepts covered in this {language} learning content.

Text:
{text_sample}

List the grammar topics/rules discussed.
"""

        try:
            response = self.generate_response(prompt)
            extracted = self.parse_json_response(response)

            if 'grammar_points' in extracted:
                return extracted['grammar_points']
            else:
                return []

        except Exception as e:
            self.logger.warning(f"Grammar extraction failed: {e}")
            return []

    def extract_topics(self, text: str) -> Dict[str, Any]:
        """Public method to extract topics from text"""
        return self._extract_topics_with_ai(text, "Unknown")

    def identify_difficulty_level(self, text: str) -> str:
        """Estimate difficulty level of content"""
        return self.pdf_handler._estimate_difficulty(text)

