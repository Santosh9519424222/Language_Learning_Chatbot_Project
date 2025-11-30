"""
Q&A Agent
Answers questions using PDF content with language level adaptation

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import QA_AGENT_PROMPT
from config.gemini_config import GeminiClient
from storage.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class QAAgent(BaseAgent):
    """
    Agent responsible for answering questions based on PDF content.
    Adapts responses to user's language proficiency level.
    """

    def __init__(self, gemini_client: GeminiClient, vector_store: ChromaVectorStore):
        """
        Initialize Q&A Agent.

        Args:
            gemini_client: Gemini API client instance
            vector_store: ChromaDB vector store instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="QAAgent",
            system_prompt=QA_AGENT_PROMPT,
            temperature=0.7
        )
        self.vector_store = vector_store

    def process(
        self,
        pdf_id: str,
        question: str,
        user_language_level: str,
        target_language: str = "English"
    ) -> AgentResponse:
        """
        Answer question using PDF content.

        Args:
            pdf_id: PDF identifier
            question: User's question
            user_language_level: User's proficiency (Beginner/Intermediate/Advanced)
            target_language: Language for response

        Returns:
            AgentResponse: Answer with source citations
        """
        start_time = time.time()

        try:
            self.logger.info(f"Processing question for PDF {pdf_id}: '{question[:50]}...'")

            # Step 1: Retrieve relevant context from vector store
            context_chunks = self.retrieve_context(pdf_id, question, top_k=5)

            if not context_chunks:
                return AgentResponse(
                    success=True,
                    data={
                        'answer': "I couldn't find relevant information in the PDF to answer your question.",
                        'source_section': None,
                        'page_number': None,
                        'confidence': 0.0,
                        'language_level': user_language_level,
                        'no_context': True
                    },
                    agent_name=self.agent_name,
                    duration=time.time() - start_time
                )

            # Step 2: Generate answer using AI
            answer_data = self._generate_answer(
                question=question,
                context_chunks=context_chunks,
                language_level=user_language_level,
                target_language=target_language
            )

            # Step 3: Calculate confidence score
            confidence = self.calculate_confidence(answer_data, context_chunks)
            answer_data['confidence'] = confidence

            duration = time.time() - start_time
            self.log_performance('question_answering', duration, True)

            self.logger.info(
                f"Question answered",
                extra={
                    'pdf_id': pdf_id,
                    'confidence': confidence,
                    'language_level': user_language_level,
                    'duration': duration
                }
            )

            return AgentResponse(
                success=True,
                data=answer_data,
                agent_name=self.agent_name,
                duration=duration
            )

        except Exception as e:
            self.logger.error(f"Question answering failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def retrieve_context(self, pdf_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks from vector store.

        Args:
            pdf_id: PDF identifier
            query: Search query
            top_k: Number of chunks to retrieve

        Returns:
            List[Dict]: Relevant chunks with metadata
        """
        try:
            chunks = self.vector_store.retrieve_relevant_chunks(
                query=query,
                pdf_id=pdf_id,
                top_k=top_k
            )

            self.logger.debug(f"Retrieved {len(chunks)} context chunks")
            return chunks

        except Exception as e:
            self.logger.error(f"Context retrieval failed: {e}")
            return []

    def _generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        language_level: str,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Generate answer using AI with context.

        Args:
            question: User's question
            context_chunks: Retrieved context
            language_level: User's proficiency level
            target_language: Response language

        Returns:
            dict: Answer data
        """
        # Format context
        context_text = "\n\n".join([
            f"[Page {chunk['page']}] {chunk['content']}"
            for chunk in context_chunks
        ])

        # Get source info from best chunk
        best_chunk = context_chunks[0] if context_chunks else {}

        prompt = f"""
User's Language Level: {language_level}
Target Language: {target_language}

Context from PDF:
{context_text}

User's Question: {question}

Answer the question using ONLY the provided context. Adapt your explanation to the {language_level} level.
"""

        try:
            response = self.generate_response(prompt)
            answer_data = self.parse_json_response(response)

            # Ensure required fields
            if 'answer' not in answer_data:
                answer_data['answer'] = response[:500]  # Use raw response if JSON parsing failed

            if 'source_section' not in answer_data:
                answer_data['source_section'] = "PDF Content"

            if 'page_number' not in answer_data:
                answer_data['page_number'] = best_chunk.get('page', None)

            answer_data['language_level'] = language_level
            answer_data['source_chunks'] = [
                {
                    'text': chunk['content'][:200],
                    'page': chunk['page'],
                    'confidence': 1.0 - chunk.get('distance', 0.5)
                }
                for chunk in context_chunks[:3]
            ]

            return answer_data

        except Exception as e:
            self.logger.error(f"Answer generation failed: {e}")
            raise

    def calculate_confidence(self, answer_data: Dict[str, Any], context_chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for answer.

        Args:
            answer_data: Generated answer data
            context_chunks: Context used

        Returns:
            float: Confidence score (0.0-1.0)
        """
        if not context_chunks:
            return 0.0

        # Base confidence on semantic similarity (distance)
        avg_distance = sum(chunk.get('distance', 0.5) for chunk in context_chunks) / len(context_chunks)
        similarity_score = 1.0 - min(avg_distance, 1.0)

        # Adjust based on answer length (very short answers are suspicious)
        answer_length = len(answer_data.get('answer', ''))
        length_factor = min(answer_length / 100, 1.0)

        # Combine factors
        confidence = (similarity_score * 0.7) + (length_factor * 0.3)

        return round(confidence, 2)

    def adjust_for_language_level(self, answer: str, user_level: str) -> str:
        """
        Adjust answer complexity for user's language level.

        Args:
            answer: Original answer
            user_level: User's proficiency level

        Returns:
            str: Adjusted answer
        """
        # This is a simplified version; in production, you'd use AI to rewrite
        if user_level == "Beginner":
            prompt = f"Simplify this answer for a beginner language learner:\n\n{answer}"
        elif user_level == "Advanced":
            prompt = f"Enhance this answer with more sophisticated language:\n\n{answer}"
        else:
            return answer  # Intermediate - keep as is

        try:
            adjusted = self.generate_response(prompt, temperature=0.5)
            return adjusted
        except Exception as e:
            self.logger.warning(f"Level adjustment failed: {e}")
            return answer

