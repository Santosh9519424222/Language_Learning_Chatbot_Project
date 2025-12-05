"""
QA Agent
Answers questions about PDF content

Author: Santosh Yadav
Date: November 2025
"""

import logging
from .base_agent import LLMAgent, StorageAgent, AgentResponse

logger = logging.getLogger(__name__)


class QAAgent(LLMAgent, StorageAgent):
    """
    Agent for question answering about PDF content.
    """

    def __init__(self, gemini_client, vector_store=None, model: str = "gemini-pro"):
        LLMAgent.__init__(self, gemini_client, name="qa", model=model)
        self.vector_store = vector_store

    def process(self, **kwargs) -> AgentResponse:
        """Answer questions about PDF content."""
        try:
            question = kwargs.get('question', '')
            pdf_id = kwargs.get('pdf_id', '')

            if not question:
                return self._create_response(success=False, error="Missing question")

            # Try to get context from vector store
            context = ""
            if self.vector_store and pdf_id:
                success, results = self.search_similar(question, pdf_id, top_k=3)
                if success and results:
                    context = "\n".join([r.get('text', '') for r in results[:3]])

            # Generate answer
            prompt = f"""Answer this question based on the provided context:
Question: {question}

Context:
{context if context else 'No specific context available'}

Provide a clear, concise answer."""

            success, response = self.generate_text(prompt, temperature=0.5, max_tokens=500)

            if success:
                return self._create_response(
                    success=True,
                    data={
                        'answer': response,
                        'confidence': 0.8,
                        'source_page': 1
                    }
                )

            return self._create_response(success=False, error="Answer generation failed")
        except Exception as e:
            return self._create_response(success=False, error=str(e))

