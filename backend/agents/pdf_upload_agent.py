"""
PDF Upload Agent
Handles PDF validation, metadata extraction, and language detection

Author: Santosh Yadav
Date: November 2025
"""

import logging
from typing import Optional
from .base_agent import LLMAgent, AgentResponse

logger = logging.getLogger(__name__)


class PDFUploadAgent(LLMAgent):
    """
    Agent for handling PDF uploads and initial processing.

    Responsibilities:
    - Validate PDF format and integrity
    - Extract metadata (title, author, creation date)
    - Detect language
    - Extract basic text
    - Identify document topic
    """

    def __init__(self, gemini_client, model: str = "gemini-pro"):
        """
        Initialize PDF Upload Agent.

        Args:
            gemini_client: Initialized GeminiClient
            model: LLM model to use
        """
        super().__init__(gemini_client, name="pdf_upload", model=model)

    def process(
        self,
        file_path: str,
        user_id: str,
        enable_ocr: bool = False
    ) -> AgentResponse:
        """
        Process uploaded PDF file.

        Args:
            file_path: Path to PDF file
            user_id: User identifier
            enable_ocr: Whether to enable OCR for image-based PDFs

        Returns:
            AgentResponse with extracted metadata
        """
        import time
        start_time = time.time()

        try:
            # Import here to avoid circular imports
            from storage.pdf_handler import validate_pdf, extract_text_from_pdf, get_pdf_metadata

            # Step 1: Validate PDF
            validation_result = validate_pdf(file_path)
            if not validation_result.get('valid'):
                return self._create_response(
                    success=False,
                    error=validation_result.get('error', 'PDF validation failed'),
                    execution_time=time.time() - start_time
                )

            # Step 2: Extract metadata
            metadata = get_pdf_metadata(file_path)

            # Step 3: Extract text
            extraction_result = extract_text_from_pdf(file_path)
            full_text = extraction_result.get('full_text', '')[:5000]  # Limit for LLM

            # Step 4: Detect language
            detected_language = extraction_result.get('detected_language', 'en')

            # Step 5: AI analysis of content
            ai_analysis = self._analyze_content_with_ai(full_text)

            response_data = {
                'file_size': validation_result.get('file_size', 0),
                'page_count': validation_result.get('page_count', 0),
                'detected_language': detected_language,
                'metadata': metadata,
                'extraction_status': 'success' if extraction_result.get('full_text') else 'partial',
                'ai_analysis': ai_analysis,
                'warnings': validation_result.get('warnings', [])
            }

            execution_time = time.time() - start_time
            return self._create_response(
                success=True,
                data=response_data,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"PDF processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._create_response(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )

    def _analyze_content_with_ai(self, text: str) -> dict:
        """
        Use Gemini AI to analyze PDF content.

        Args:
            text: Extracted text from PDF

        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = f"""Analyze this PDF text and provide:
1. Main topic (one-liner)
2. Estimated difficulty level (Beginner/Intermediate/Advanced)
3. Key subjects covered (comma-separated)
4. Language of the document (ISO 639-1 code)

Text:
{text[:2000]}

Respond in JSON format:
{{"topic": "...", "difficulty": "...", "subjects": "...", "language": "..."}}"""

            success, response = self.generate_text(prompt, temperature=0.3, max_tokens=500)

            if success:
                success, parsed = self.parse_json_response(response)
                if success:
                    return parsed

            # Fallback analysis
            return {
                'topic': 'Document',
                'difficulty': 'Intermediate',
                'subjects': 'General',
                'language': 'en'
            }

        except Exception as e:
            logger.warning(f"AI analysis failed: {str(e)}, using defaults")
            return {
                'topic': 'Document',
                'difficulty': 'Intermediate',
                'subjects': 'General',
                'language': 'en'
            }

