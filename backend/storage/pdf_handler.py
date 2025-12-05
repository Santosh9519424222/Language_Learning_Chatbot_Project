"""
PDF Handler Module
Comprehensive PDF processing, validation, and text extraction

Author: Santosh Yadav
Date: November 2025
"""

import os
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path

import pdfplumber
from PyPDF2 import PdfReader
from langdetect import detect, detect_langs, LangDetectException

# Optional imports - make them fail gracefully
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic not installed. PDF validation will be limited.")

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logger.warning("pytesseract or PIL not installed. OCR features will be disabled.")

logger = logging.getLogger(__name__)


class PDFHandler:
    """
    Handles all PDF-related operations including validation, extraction, and processing.
    """

    # Constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_PAGES = 500
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Supported language codes mapping
    LANGUAGE_CODES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'zh-cn': 'Chinese',
        'zh-tw': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'hi': 'Hindi',
        'pt': 'Portuguese',
        'ar': 'Arabic'
    }

    @staticmethod
    def validate_pdf(file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file format, size, and page count.

        Args:
            file_path: Path to PDF file

        Returns:
            dict: {
                'valid': bool,
                'error': str or None,
                'page_count': int,
                'file_size': int,
                'warnings': List[str]
            }
        """
        logger.info(f"Validating PDF: {file_path}")

        result = {
            'valid': False,
            'error': None,
            'page_count': 0,
            'file_size': 0,
            'warnings': []
        }

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['error'] = "File does not exist"
                logger.error(f"File not found: {file_path}")
                return result

            # Check file size
            file_size = os.path.getsize(file_path)
            result['file_size'] = file_size

            if file_size == 0:
                result['error'] = "File is empty"
                logger.error(f"Empty file: {file_path}")
                return result

            if file_size > PDFHandler.MAX_FILE_SIZE:
                result['error'] = f"File size exceeds maximum allowed ({PDFHandler.MAX_FILE_SIZE / (1024*1024):.0f} MB)"
                logger.error(f"File too large: {file_size} bytes")
                return result

            # Validate PDF magic bytes
            try:
                mime = magic.from_file(file_path, mime=True)
                if mime != 'application/pdf':
                    result['error'] = f"Invalid file type: {mime}. Expected PDF."
                    logger.error(f"Invalid file type: {mime}")
                    return result
            except Exception as e:
                logger.warning(f"Magic bytes validation failed: {e}")
                result['warnings'].append("Could not verify file type with magic bytes")

            # Check page count
            try:
                with pdfplumber.open(file_path) as pdf:
                    page_count = len(pdf.pages)
                    result['page_count'] = page_count

                    if page_count == 0:
                        result['error'] = "PDF has no pages"
                        logger.error(f"PDF has no pages: {file_path}")
                        return result

                    if page_count > PDFHandler.MAX_PAGES:
                        result['error'] = f"PDF has too many pages ({page_count}). Maximum allowed: {PDFHandler.MAX_PAGES}"
                        logger.error(f"Too many pages: {page_count}")
                        return result

                    # Check if pages are extractable
                    sample_text = pdf.pages[0].extract_text()
                    if not sample_text or len(sample_text.strip()) < 10:
                        result['warnings'].append("First page has very little extractable text. PDF may be image-based.")
                        logger.warning("First page has minimal text")

            except Exception as e:
                result['error'] = f"Failed to read PDF: {str(e)}"
                logger.error(f"PDF reading error: {e}", exc_info=True)
                return result

            # All checks passed
            result['valid'] = True
            logger.info(f"PDF validation successful: {page_count} pages, {file_size} bytes")

        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"
            logger.error(f"Validation exception: {e}", exc_info=True)

        return result

    @staticmethod
    def extract_text_from_pdf(file_path: str, enable_ocr: bool = False) -> Dict[str, Any]:
        """
        Extract full text and metadata from PDF, with optional OCR for image-based pages.

        Args:
            file_path: Path to PDF file
            enable_ocr: Enable OCR processing for image-based PDFs

        Returns:
            dict: {
                'full_text': str,
                'pages_count': int,
                'metadata': dict,
                'text_by_page': List[dict],
                'extraction_time': float,
                'detected_language': str,
                'language_confidence': float
            }
        """
        logger.info(f"Extracting text from PDF: {file_path}")
        start_time = time.time()

        result = {
            'full_text': '',
            'pages_count': 0,
            'metadata': {},
            'text_by_page': [],
            'extraction_time': 0.0,
            'detected_language': 'Unknown',
            'language_confidence': 0.0
        }

        try:
            with pdfplumber.open(file_path) as pdf:
                result['pages_count'] = len(pdf.pages)

                all_text = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""

                    # If no text and OCR enabled, try OCR on the rasterized page
                    if enable_ocr and (not page_text or len(page_text.strip()) < 10):
                        try:
                            im = page.to_image(resolution=200).original
                            ocr_text = pytesseract.image_to_string(im)
                            if ocr_text and len(ocr_text.strip()) > 0:
                                page_text = ocr_text
                                logger.info(f"OCR extracted text on page {i+1}")
                        except Exception as ocr_err:
                            logger.warning(f"OCR failed on page {i+1}: {ocr_err}")

                    all_text.append(page_text)

                    result['text_by_page'].append({
                        'page_number': i + 1,
                        'text': page_text,
                        'word_count': len(page_text.split()),
                        'char_count': len(page_text)
                    })

                result['full_text'] = '\n\n'.join(all_text)

                # Extract metadata
                result['metadata'] = PDFHandler.get_pdf_metadata(file_path)

                # Detect language
                if result['full_text'].strip():
                    lang_result = PDFHandler._detect_language(result['full_text'][:5000])  # Use first 5000 chars
                    result['detected_language'] = lang_result['language']
                    result['language_confidence'] = lang_result['confidence']

                result['extraction_time'] = time.time() - start_time

                logger.info(
                    f"Extraction complete: {result['pages_count']} pages, "
                    f"{len(result['full_text'])} chars, "
                    f"language: {result['detected_language']}, "
                    f"time: {result['extraction_time']:.2f}s"
                )

        except Exception as e:
            logger.error(f"Text extraction error: {e}", exc_info=True)
            raise

        return result

    @staticmethod
    def extract_text_chunks(
        file_path: str,
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP
    ) -> List[Dict[str, Any]]:
        """
        Extract text in overlapping chunks for semantic search.

        Args:
            file_path: Path to PDF file
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters

        Returns:
            List[dict]: List of chunks with metadata
        """
        logger.info(f"Extracting text chunks from: {file_path}")

        chunks = []

        try:
            extraction_result = PDFHandler.extract_text_from_pdf(file_path)
            text_by_page = extraction_result['text_by_page']

            chunk_id = 0

            for page_data in text_by_page:
                page_num = page_data['page_number']
                page_text = page_data['text']

                if not page_text.strip():
                    continue

                # Split page text into chunks with overlap
                start = 0
                while start < len(page_text):
                    end = start + chunk_size
                    chunk_text = page_text[start:end]

                    if chunk_text.strip():
                        # Determine if chunk contains vocabulary indicators
                        is_vocabulary = PDFHandler._is_vocabulary_section(chunk_text)

                        # Estimate difficulty
                        difficulty = PDFHandler._estimate_difficulty(chunk_text)

                        chunks.append({
                            'chunk_id': f"{os.path.basename(file_path)}_{page_num}_{chunk_id}",
                            'text': chunk_text.strip(),
                            'page': page_num,
                            'start_char': start,
                            'end_char': end,
                            'is_vocabulary': is_vocabulary,
                            'difficulty': difficulty,
                            'word_count': len(chunk_text.split())
                        })

                        chunk_id += 1

                    start = end - overlap if end < len(page_text) else len(page_text)

            logger.info(f"Extracted {len(chunks)} chunks from {len(text_by_page)} pages")

        except Exception as e:
            logger.error(f"Chunk extraction error: {e}", exc_info=True)
            raise

        return chunks

    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata.

        Args:
            file_path: Path to PDF file

        Returns:
            dict: Metadata including title, author, subject, etc.
        """
        metadata = {
            'title': None,
            'author': None,
            'subject': None,
            'creator': None,
            'producer': None,
            'creation_date': None,
            'modification_date': None
        }

        try:
            reader = PdfReader(file_path)
            info = reader.metadata

            if info:
                metadata['title'] = str(info.get('/Title', '')).strip() or None
                metadata['author'] = str(info.get('/Author', '')).strip() or None
                metadata['subject'] = str(info.get('/Subject', '')).strip() or None
                metadata['creator'] = str(info.get('/Creator', '')).strip() or None
                metadata['producer'] = str(info.get('/Producer', '')).strip() or None
                metadata['creation_date'] = str(info.get('/CreationDate', '')).strip() or None
                metadata['modification_date'] = str(info.get('/ModDate', '')).strip() or None

            logger.debug(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")

        return metadata

    @staticmethod
    def save_uploaded_pdf(uploaded_file, destination_folder: str) -> str:
        """
        Save uploaded PDF file with UUID naming.

        Args:
            uploaded_file: FastAPI UploadFile object
            destination_folder: Folder to save file

        Returns:
            str: Full path to saved file
        """
        try:
            # Create destination folder if not exists
            os.makedirs(destination_folder, exist_ok=True)

            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(destination_folder, unique_filename)

            # Save file
            with open(file_path, "wb") as f:
                content = uploaded_file.file.read()
                f.write(content)

            logger.info(f"Saved uploaded file: {file_path} ({len(content)} bytes)")

            return file_path

        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
            raise

    @staticmethod
    def delete_pdf_file(file_path: str) -> bool:
        """
        Safely delete PDF file.

        Args:
            file_path: Path to file

        Returns:
            bool: True if deleted successfully
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file: {e}", exc_info=True)
            return False

    # Helper Methods

    @staticmethod
    def _detect_language(text: str) -> Dict[str, Any]:
        """
        Detect language of text.

        Args:
            text: Text to analyze

        Returns:
            dict: {'language': str, 'confidence': float}
        """
        if not text or len(text.strip()) < 50:
            return {'language': 'Unknown', 'confidence': 0.0}

        try:
            # Get language probabilities
            lang_probs = detect_langs(text)

            if lang_probs:
                top_lang = lang_probs[0]
                lang_code = top_lang.lang
                confidence = top_lang.prob

                # Map to full language name
                language_name = PDFHandler.LANGUAGE_CODES.get(lang_code, lang_code.upper())

                logger.debug(f"Detected language: {language_name} (confidence: {confidence:.2f})")

                return {
                    'language': language_name,
                    'confidence': confidence
                }
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
        except Exception as e:
            logger.error(f"Language detection error: {e}", exc_info=True)

        return {'language': 'Unknown', 'confidence': 0.0}

    @staticmethod
    def _is_vocabulary_section(text: str) -> bool:
        """
        Determine if text chunk is a vocabulary section.

        Args:
            text: Text chunk

        Returns:
            bool: True if appears to be vocabulary section
        """
        vocabulary_indicators = [
            'vocabulary',
            'vocabulario',
            'vocabulaire',
            'wortschatz',
            'glossary',
            'glosario',
            'terms',
            'definitions',
            'palabras clave',
            'key words',
            'word list'
        ]

        text_lower = text.lower()

        # Check for vocabulary indicators
        for indicator in vocabulary_indicators:
            if indicator in text_lower:
                return True

        # Check for definition patterns (word: definition or word - definition)
        definition_patterns = text.count(':') + text.count(' - ')
        if definition_patterns > 3:  # Multiple definitions indicate vocabulary
            return True

        return False

    @staticmethod
    def _estimate_difficulty(text: str) -> str:
        """
        Estimate difficulty level of text.

        Args:
            text: Text to analyze

        Returns:
            str: Difficulty level (Beginner/Intermediate/Advanced)
        """
        words = text.split()

        if len(words) < 10:
            return "Beginner"

        # Simple heuristic based on average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        if avg_word_length < 4.5:
            return "Beginner"
        elif avg_word_length < 6.0:
            return "Intermediate"
        else:
            return "Advanced"


# Module-level convenience functions

def validate_pdf(file_path: str) -> Dict[str, Any]:
    """Validate a PDF file."""
    return PDFHandler.validate_pdf(file_path)


def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract text from a PDF file."""
    return PDFHandler.extract_text_from_pdf(file_path)


def extract_text_chunks(file_path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Extract text chunks from a PDF file."""
    return PDFHandler.extract_text_chunks(file_path, chunk_size, overlap)


def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """Get PDF metadata."""
    return PDFHandler.get_pdf_metadata(file_path)


def save_uploaded_pdf(uploaded_file, destination_folder: str) -> str:
    """Save an uploaded PDF file."""
    return PDFHandler.save_uploaded_pdf(uploaded_file, destination_folder)


def delete_pdf_file(file_path: str) -> bool:
    """Delete a PDF file."""
    return PDFHandler.delete_pdf_file(file_path)
