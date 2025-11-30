"""
Pydantic Request/Response Schemas
Type-safe API contracts with validation

Author: Santosh Yadav
Date: November 2025
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum


# Enums
class LanguageLevel(str, Enum):
    """Language proficiency levels"""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class MistakeType(str, Enum):
    """Types of language mistakes"""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    FLUENCY = "fluency"
    SYNTAX = "syntax"


class PDFStatus(str, Enum):
    """PDF processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SupportedLanguage(str, Enum):
    """Supported languages"""
    ENGLISH = "English"
    FRENCH = "French"
    SPANISH = "Spanish"
    GERMAN = "German"
    ITALIAN = "Italian"
    CHINESE = "Chinese"
    JAPANESE = "Japanese"
    KOREAN = "Korean"
    HINDI = "Hindi"
    PORTUGUESE = "Portuguese"
    ARABIC = "Arabic"


# ==================== PDF SCHEMAS ====================

class PDFUploadRequest(BaseModel):
    """Request schema for PDF upload"""
    language: Optional[str] = Field(
        None,
        description="Language of the PDF (auto-detected if not provided)",
        example="English"
    )
    user_id: UUID = Field(..., description="User ID uploading the PDF")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "language": "English",
                "user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class PDFUploadResponse(BaseModel):
    """Response schema for PDF upload"""
    file_id: UUID = Field(..., description="Unique PDF identifier")
    filename: str = Field(..., description="Original filename")
    status: PDFStatus = Field(..., description="Processing status")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    file_size: int = Field(..., description="File size in bytes")
    total_pages: int = Field(..., description="Number of pages")
    detected_language: Optional[str] = Field(None, description="Auto-detected language")
    message: str = Field(..., description="Status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "spanish_grammar.pdf",
                "status": "processing",
                "upload_timestamp": "2025-11-30T10:30:00Z",
                "file_size": 2048576,
                "total_pages": 45,
                "detected_language": "Spanish",
                "message": "PDF uploaded successfully and queued for processing"
            }
        }
    )


class VocabularyItem(BaseModel):
    """Individual vocabulary item"""
    word: str = Field(..., description="The vocabulary word")
    definition: str = Field(..., description="Definition in target language")
    difficulty: str = Field(..., description="Difficulty level")
    example_sentence: Optional[str] = Field(None, description="Example usage")
    pronunciation: Optional[str] = Field(None, description="Pronunciation guide")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "word": "comprehensión",
                "definition": "understanding or grasp of knowledge",
                "difficulty": "Intermediate",
                "example_sentence": "La comprehensión lectora es importante.",
                "pronunciation": "kom-preh-en-see-ON"
            }
        }
    )


class TopicItem(BaseModel):
    """Individual topic extracted from PDF"""
    name: str = Field(..., description="Topic name")
    description: str = Field(..., description="Topic description")
    page_number: int = Field(..., description="Page where topic appears")
    hierarchy_level: int = Field(..., description="Topic hierarchy level (1=main, 2=sub, etc.)")
    difficulty: LanguageLevel = Field(..., description="Difficulty level")
    vocabulary: List[VocabularyItem] = Field(default_factory=list, description="Key vocabulary")
    grammar_points: List[str] = Field(default_factory=list, description="Grammar concepts")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Present Tense Conjugation",
                "description": "Learn regular and irregular verb conjugations in present tense",
                "page_number": 12,
                "hierarchy_level": 1,
                "difficulty": "Beginner",
                "vocabulary": [
                    {"word": "hablar", "definition": "to speak", "difficulty": "Beginner"}
                ],
                "grammar_points": ["Regular -ar verbs", "Subject pronouns"]
            }
        }
    )


class TopicsListResponse(BaseModel):
    """Response schema for extracted topics list"""
    file_id: UUID = Field(..., description="PDF identifier")
    topics: List[TopicItem] = Field(..., description="List of extracted topics")
    summary: str = Field(..., description="Overall content summary")
    total_pages: int = Field(..., description="Total pages in PDF")
    total_topics: int = Field(..., description="Number of topics extracted")
    extraction_timestamp: datetime = Field(..., description="When topics were extracted")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "topics": [],
                "summary": "Spanish grammar guide covering verb conjugations and tenses",
                "total_pages": 45,
                "total_topics": 12,
                "extraction_timestamp": "2025-11-30T10:35:00Z"
            }
        }
    )


# ==================== Q&A SCHEMAS ====================

class QuestionRequest(BaseModel):
    """Request schema for asking questions"""
    file_id: UUID = Field(..., description="PDF identifier")
    user_id: UUID = Field(..., description="User identifier")
    question: str = Field(..., min_length=3, max_length=500, description="User's question")
    language: str = Field(..., description="Language for response")
    user_language_level: LanguageLevel = Field(..., description="User's proficiency level")

    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "question": "How do I conjugate regular -ar verbs in present tense?",
                "language": "English",
                "user_language_level": "Beginner"
            }
        }
    )


class SourceChunk(BaseModel):
    """Source text chunk with metadata"""
    text: str = Field(..., description="Text content")
    page: int = Field(..., description="Page number")
    confidence: float = Field(..., description="Relevance score")


class QuestionResponse(BaseModel):
    """Response schema for Q&A"""
    answer: str = Field(..., description="AI-generated answer")
    source_section: str = Field(..., description="Section/topic from which answer derived")
    page_number: Optional[int] = Field(None, description="Page reference")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    source_chunks: List[SourceChunk] = Field(..., description="Source text chunks used")
    language_level: LanguageLevel = Field(..., description="Language level of answer")
    session_id: UUID = Field(..., description="Q&A session identifier")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "To conjugate regular -ar verbs in present tense, remove the -ar ending and add: -o, -as, -a, -amos, -áis, -an",
                "source_section": "Present Tense Conjugation",
                "page_number": 12,
                "confidence_score": 0.95,
                "source_chunks": [],
                "language_level": "Beginner",
                "session_id": "123e4567-e89b-12d3-a456-426614174002"
            }
        }
    )


# ==================== LANGUAGE COACHING SCHEMAS ====================

class LanguageFeedbackRequest(BaseModel):
    """Request schema for language feedback"""
    user_id: UUID = Field(..., description="User identifier")
    pdf_id: Optional[UUID] = Field(None, description="PDF identifier (optional)")
    user_output: str = Field(..., description="User's language output to analyze")
    correct_form: Optional[str] = Field(None, description="Correct form if known")
    context: Optional[str] = Field(None, description="Context of the output")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "pdf_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_output": "Yo hablar español",
                "correct_form": None,
                "context": "Trying to say 'I speak Spanish'"
            }
        }
    )


class VocabularySuggestion(BaseModel):
    """Vocabulary suggestion with alternatives"""
    original: str = Field(..., description="Original word/phrase")
    suggestions: List[str] = Field(..., description="Better alternatives")
    explanation: str = Field(..., description="Why suggestion is better")


class LanguageFeedbackResponse(BaseModel):
    """Response schema for language feedback"""
    grammar_feedback: str = Field(..., description="Grammar corrections and explanations")
    vocabulary_suggestions: List[VocabularySuggestion] = Field(
        default_factory=list,
        description="Vocabulary improvement suggestions"
    )
    fluency_notes: str = Field(..., description="Fluency and naturalness feedback")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in feedback")
    encouragement: str = Field(..., description="Encouraging message for learner")
    mistakes_logged: int = Field(..., description="Number of mistakes logged to database")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "grammar_feedback": "Use 'hablo' instead of 'hablar'. In Spanish, verbs must be conjugated to match the subject.",
                "vocabulary_suggestions": [
                    {
                        "original": "hablar",
                        "suggestions": ["hablo"],
                        "explanation": "First person singular present tense conjugation"
                    }
                ],
                "fluency_notes": "Good attempt! Remember to conjugate verbs.",
                "confidence": 0.95,
                "encouragement": "You're making great progress! Keep practicing verb conjugations.",
                "mistakes_logged": 1
            }
        }
    )


# ==================== TRANSLATION SCHEMAS ====================

class TranslationRequest(BaseModel):
    """Request schema for translation"""
    file_id: UUID = Field(..., description="PDF identifier")
    target_language: str = Field(..., description="Target language")
    include_pronunciation: bool = Field(default=True, description="Include pronunciation guides")

    @validator('target_language')
    def validate_language(cls, v):
        valid_languages = [lang.value for lang in SupportedLanguage]
        if v not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_language": "Hindi",
                "include_pronunciation": True
            }
        }
    )


class TranslatedTopic(BaseModel):
    """Translated topic item"""
    original_name: str
    translated_name: str
    original_description: str
    translated_description: str
    pronunciation: Optional[str] = None


class TranslationResponse(BaseModel):
    """Response schema for translation"""
    translation_id: UUID = Field(..., description="Translation identifier")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    translated_topics: List[TranslatedTopic] = Field(..., description="Translated topics")
    download_url: Optional[str] = Field(None, description="Download URL for full translation")
    translation_timestamp: datetime = Field(..., description="When translation was completed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "translation_id": "123e4567-e89b-12d3-a456-426614174003",
                "source_language": "Spanish",
                "target_language": "Hindi",
                "translated_topics": [],
                "download_url": "/api/downloads/translations/123e4567-e89b-12d3-a456-426614174003.pdf",
                "translation_timestamp": "2025-11-30T10:40:00Z"
            }
        }
    )


# ==================== LEARNING REPORT SCHEMAS ====================

class LearningGap(BaseModel):
    """Individual learning gap"""
    topic: str = Field(..., description="Topic/concept with gap")
    description: str = Field(..., description="Description of the gap")
    severity: str = Field(..., description="Low/Medium/High")
    recommendations: List[str] = Field(..., description="How to address this gap")


class LearningReportResponse(BaseModel):
    """Response schema for learning reports"""
    report_id: UUID = Field(..., description="Report identifier")
    user_id: UUID = Field(..., description="User identifier")
    summary: str = Field(..., description="Overall learning summary")
    learning_gaps: List[LearningGap] = Field(..., description="Identified learning gaps")
    accuracy_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall accuracy")
    total_sessions: int = Field(..., description="Total Q&A sessions analyzed")
    total_mistakes: int = Field(..., description="Total mistakes logged")
    most_common_mistake_type: str = Field(..., description="Most frequent mistake type")
    recommendations: List[str] = Field(..., description="Personalized recommendations")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    download_url: Optional[str] = Field(None, description="PDF download URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "123e4567-e89b-12d3-a456-426614174004",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "summary": "You've made excellent progress with basic grammar!",
                "learning_gaps": [
                    {
                        "topic": "Irregular Verbs",
                        "description": "Difficulty with irregular verb conjugations",
                        "severity": "Medium",
                        "recommendations": ["Practice top 20 irregular verbs daily"]
                    }
                ],
                "accuracy_percentage": 78.5,
                "total_sessions": 25,
                "total_mistakes": 12,
                "most_common_mistake_type": "grammar",
                "recommendations": ["Focus on verb conjugations", "Practice daily for 15 minutes"],
                "generated_at": "2025-11-30T10:45:00Z",
                "download_url": "/api/downloads/reports/123e4567-e89b-12d3-a456-426614174004.pdf"
            }
        }
    )


# ==================== MISTAKE LOGGING SCHEMAS ====================

class MistakeLogRequest(BaseModel):
    """Request schema for logging mistakes"""
    user_id: UUID = Field(..., description="User identifier")
    pdf_id: Optional[UUID] = Field(None, description="PDF identifier")
    mistake_text: str = Field(..., description="The incorrect text")
    correction: str = Field(..., description="Corrected version")
    mistake_type: MistakeType = Field(..., description="Type of mistake")
    context: Optional[str] = Field(None, description="Context of mistake")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "pdf_id": "123e4567-e89b-12d3-a456-426614174000",
                "mistake_text": "Yo hablar",
                "correction": "Yo hablo",
                "mistake_type": "grammar",
                "context": "Present tense conjugation"
            }
        }
    )


class MistakeLogResponse(BaseModel):
    """Response schema for mistake logging"""
    id: UUID = Field(..., description="Mistake log identifier")
    confidence_score: float = Field(..., description="Confidence in correction")
    feedback: str = Field(..., description="Detailed feedback")
    timestamp: datetime = Field(..., description="When mistake was logged")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174005",
                "confidence_score": 0.98,
                "feedback": "Remember to conjugate verbs. 'Hablar' is infinitive, use 'hablo' for 'I speak'.",
                "timestamp": "2025-11-30T10:50:00Z"
            }
        }
    )


# ==================== HEALTH & STATUS SCHEMAS ====================

class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str = Field(..., description="Overall status")
    timestamp: datetime = Field(..., description="Check timestamp")
    environment: str = Field(..., description="Environment (dev/prod)")
    agents_active: int = Field(..., description="Number of active agents")
    services: Dict[str, str] = Field(..., description="Service statuses")
    gemini_quota: Dict[str, Any] = Field(..., description="Gemini API quota info")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-30T10:55:00Z",
                "environment": "production",
                "agents_active": 7,
                "services": {
                    "database": "healthy",
                    "vector_store": "healthy",
                    "gemini_api": "healthy"
                },
                "gemini_quota": {
                    "available": True,
                    "requests_remaining": 58,
                    "reset_time": "2025-11-30T11:00:00Z"
                }
            }
        }
    )


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """Request schema for creating a user"""
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    language_focus: str = Field(...)
    proficiency_level: LanguageLevel = Field(default=LanguageLevel.BEGINNER)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "santosh_learner",
                "email": "santosh@example.com",
                "language_focus": "Spanish",
                "proficiency_level": "Beginner"
            }
        }
    )


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: UUID
    username: str
    email: str
    language_focus: str
    proficiency_level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

