"""
PDF Upload Agent
Validates PDFs, extracts metadata, detects language

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import PDF_UPLOAD_AGENT_PROMPT
from config.gemini_config import GeminiClient
from storage.pdf_handler import PDFHandler

logger = logging.getLogger(__name__)


class PDFUploadAgent(BaseAgent):
    """
    Agent responsible for validating and analyzing uploaded PDFs.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize PDF Upload Agent.

        Args:
            gemini_client: Gemini API client instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="PDFUploadAgent",
            system_prompt=PDF_UPLOAD_AGENT_PROMPT,
            temperature=0.3  # Lower temperature for more consistent validation
        )
        self.pdf_handler = PDFHandler()

    def process(self, file_path: str, user_id: str, enable_ocr: bool = False) -> AgentResponse:
        """
        Process uploaded PDF with optional OCR.

        Args:
            file_path: Path to uploaded PDF file
            user_id: User identifier
            enable_ocr: Flag to enable OCR processing

        Returns:
            AgentResponse: Validation results and metadata
        """
        start_time = time.time()

        try:
            self.logger.info(f"Processing PDF upload: {file_path}")

            # Step 1: Validate PDF file
            validation_result = self.pdf_handler.validate_pdf(file_path)

            if not validation_result['valid']:
                return AgentResponse(
                    success=False,
                    error=validation_result['error'],
                    agent_name=self.agent_name,
                    duration=time.time() - start_time
                )

            # Step 2: Extract text and metadata
            extraction_result = self.pdf_handler.extract_text_from_pdf(file_path, enable_ocr=enable_ocr)

            # Step 3: Get AI analysis of content
            text_sample = extraction_result['full_text'][:3000]  # First 3000 chars

            ai_prompt = f"""
Analyze this PDF content sample and determine:
1. Primary language
2. Main topic/subject
3. Suitability for language learning
4. Content type and difficulty

PDF Sample:
{text_sample}

Metadata:
- Pages: {extraction_result['pages_count']}
- Detected Language: {extraction_result['detected_language']}
"""

            ai_response = self.generate_response(ai_prompt)
            ai_analysis = self.parse_json_response(ai_response)

            # Combine results
            result_data = {
                'valid': True,
                'file_path': file_path,
                'user_id': user_id,
                'page_count': extraction_result['pages_count'],
                'file_size': validation_result['file_size'],
                'detected_language': extraction_result['detected_language'],
                'language_confidence': extraction_result['language_confidence'],
                'metadata': extraction_result['metadata'],
                'ai_analysis': ai_analysis,
                'warnings': validation_result.get('warnings', []),
                'extraction_time': extraction_result['extraction_time']
            }

            duration = time.time() - start_time
            self.log_performance('pdf_upload', duration, True)

            self.logger.info(
                f"PDF upload processed successfully",
                extra={
                    'file_path': file_path,
                    'pages': extraction_result['pages_count'],
                    'language': extraction_result['detected_language'],
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
            self.logger.error(f"PDF upload processing failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Quick validation without full processing"""
        return self.pdf_handler.validate_pdf(file_path)

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language of text"""
        return self.pdf_handler._detect_language(text)

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata only"""
        return self.pdf_handler.get_pdf_metadata(file_path)
