"""
API Routes for Multi-Agent PDF Intelligence Platform
Complete implementation of all 10 REST endpoints

Author: Santosh Yadav
Date: November 2025
"""

import logging
import os
import uuid
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.database import (
    get_db_session, User, PDF, Topic, QASession,
    LanguageMistake, Translation, LearningReport
)
from models.schemas import (
    PDFUploadResponse, TopicsListResponse, TopicItem, VocabularyItem,
    QuestionRequest, QuestionResponse, SourceChunk,
    LanguageFeedbackRequest, LanguageFeedbackResponse, VocabularySuggestion,
    TranslationRequest, TranslationResponse, TranslatedTopic,
    LearningReportResponse, LearningGap,
    MistakeLogRequest, MistakeLogResponse,
    UserCreate, UserResponse
)

# Avoid importing heavy modules at import time to support degraded mode
# If type checking, we can import for type hints only
if TYPE_CHECKING:
    from config.gemini_config import GeminiClient  # pragma: no cover
    from storage.vector_store import ChromaVectorStore  # pragma: no cover

logger = logging.getLogger(__name__)

router = APIRouter()

# Upload directory
UPLOAD_DIR = os.getenv("PDF_UPLOAD_DIR", "./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================== ENDPOINT 1: Upload PDF ====================

@router.post("/pdfs/upload", response_model=PDFUploadResponse, tags=["PDF Management"])
async def upload_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF file to upload"),
    user_id: str = Form(..., description="User identifier"),
    language: Optional[str] = Form(None, description="PDF language (auto-detected if not provided)"),
    enable_ocr: Optional[str] = Form("false", description="Enable OCR for image PDFs"),
    db: Session = Depends(get_db_session)
):
    """
    Upload and process a PDF document.

    This endpoint:
    1. Validates the PDF file
    2. Extracts text and metadata
    3. Detects language
    4. Extracts topics and vocabulary
    5. Creates vector embeddings
    6. Stores in database

    Returns:
        PDFUploadResponse: Upload status with file metadata
    """
    logger.info(f"PDF upload request from user: {user_id}")

    try:
        # Lazy imports to avoid heavy dependencies during app import
        from storage.pdf_handler import save_uploaded_pdf, delete_pdf_file
        from agents import PDFUploadAgent, ExtractionAgent

        # Get dependencies from app state
        gemini_client = getattr(request.app.state, 'gemini_client', None)
        vector_store = getattr(request.app.state, 'vector_store', None)

        # Step 1: Save uploaded file
        file_path = save_uploaded_pdf(file, UPLOAD_DIR)
        logger.info(f"File saved: {file_path}")

        # Step 2: Validate and analyze PDF
        if not gemini_client:
            raise HTTPException(status_code=503, detail="Gemini client not initialized")
        upload_agent = PDFUploadAgent(gemini_client)
        use_ocr = str(enable_ocr).lower() in {"true", "1", "yes"}
        upload_result = upload_agent.process(file_path, user_id, enable_ocr=use_ocr)

        # Handle agent response (can be dict or AgentResponse TypedDict)
        if isinstance(upload_result, dict):
            success = upload_result.get('success', False)
            error = upload_result.get('error')
            data = upload_result.get('data', {})
        else:
            success = getattr(upload_result, 'success', False)
            error = getattr(upload_result, 'error', None)
            data = getattr(upload_result, 'data', {})

        if not success:
            delete_pdf_file(file_path)
            raise HTTPException(status_code=400, detail=error or "PDF processing failed")

        upload_data = data

        # Step 3: Create PDF record in database
        # For SQLite compatibility, convert UUIDs to strings
        from models.database import _is_sqlite

        pdf_id = uuid.uuid4()
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid user_id format. Must be a valid UUID.")

        # Convert to string if using SQLite
        pdf_id_value = str(pdf_id) if _is_sqlite else pdf_id
        user_id_value = str(user_uuid) if _is_sqlite else user_uuid

        pdf_record = PDF(
            id=pdf_id_value,
            user_id=user_id_value,
            filename=file.filename,
            file_path=file_path,
            file_size=upload_data.get('file_size', 0),
            total_pages=upload_data.get('page_count', 1),
            status='processing',
            language=upload_data.get('detected_language', 'en'),
            detected_topic=upload_data.get('ai_analysis', {}).get('topic', 'Unknown'),
            pdf_metadata=upload_data.get('metadata', {}) or {}
        )
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)

        # Step 4: Extract topics and vocabulary (sync for now)
        if vector_store is None:
            logger.warning("Vector store not initialized; skipping chunk indexing")
            extraction_data = {"topics": []}
        else:
            extraction_agent = ExtractionAgent(gemini_client, vector_store)
            extraction_result = extraction_agent.process(
                file_path=file_path,
                pdf_id=str(pdf_record.id),
                language=upload_data['detected_language']
            )

            # Handle agent response (can be dict or object)
            if isinstance(extraction_result, dict):
                extraction_data = extraction_result.get('data', {}) if extraction_result.get('success') else {"topics": []}
            else:
                extraction_data = getattr(extraction_result, 'data', {}) if getattr(extraction_result, 'success', False) else {"topics": []}

        # Save topics to database
        for topic_data in extraction_data.get('topics', [])[:20]:
            topic = Topic(
                pdf_id=pdf_record.id,
                topic_name=topic_data.get('name', 'Untitled'),
                description=topic_data.get('description', ''),
                page_number=topic_data.get('page_number', 1),
                section_hierarchy=topic_data.get('hierarchy', {}),
                difficulty_level=topic_data.get('difficulty', 'Beginner'),
                vocabulary=topic_data.get('key_vocabulary', []),
                grammar_points=topic_data.get('grammar_points', [])
            )
            db.add(topic)

        # Update PDF status
        pdf_record.status = 'completed'
        db.commit()

        return PDFUploadResponse(
            file_id=pdf_record.id,
            filename=file.filename,
            status=pdf_record.status,
            upload_timestamp=pdf_record.upload_date,
            file_size=pdf_record.file_size,
            total_pages=pdf_record.total_pages,
            detected_language=pdf_record.language,
            message=f"PDF processed successfully. Extracted {len(extraction_data.get('topics', []))} topics."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload failed: {e}", exc_info=True)
        # Best-effort cleanup
        try:
            from storage.pdf_handler import delete_pdf_file as _delete
            if 'file_path' in locals():
                _delete(file_path)
        except Exception:
            pass

        # Return detailed error message
        error_msg = str(e)
        if 'gemini_client' in error_msg.lower():
            error_msg = "Gemini AI service not initialized. Please check API configuration."
        elif 'file' in error_msg.lower():
            error_msg = f"File processing error: {error_msg}"
        elif 'database' in error_msg.lower():
            error_msg = "Database error. Please try again later."
        else:
            error_msg = f"PDF upload failed: {error_msg}"

        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENDPOINT 2: Get Topics ====================

@router.get("/pdfs/{file_id}/topics", response_model=TopicsListResponse, tags=["PDF Management"])
async def get_pdf_topics(
    file_id: uuid.UUID,
    db: Session = Depends(get_db_session)
):
    """Get extracted topics from a PDF."""
    logger.info(f"Fetching topics for PDF: {file_id}")

    pdf = db.query(PDF).filter(PDF.id == file_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    topics = db.query(Topic).filter(Topic.pdf_id == file_id).all()
    topic_items = []
    for topic in topics:
        vocabulary_items = [
            VocabularyItem(
                word=vocab.get('word', ''),
                definition=vocab.get('definition', ''),
                difficulty=vocab.get('difficulty', 'Beginner'),
                example_sentence=vocab.get('example_sentence'),
                pronunciation=vocab.get('pronunciation')
            )
            for vocab in (topic.vocabulary or [])[:10]
        ]
        topic_items.append(TopicItem(
            name=topic.topic_name,
            description=topic.description,
            page_number=topic.page_number,
            hierarchy_level=1,
            difficulty=topic.difficulty_level,
            vocabulary=vocabulary_items,
            grammar_points=topic.grammar_points or []
        ))

    return TopicsListResponse(
        file_id=file_id,
        topics=topic_items,
        summary=f"PDF covering {len(topic_items)} main topics in {pdf.language}",
        total_pages=pdf.total_pages,
        total_topics=len(topic_items),
        extraction_timestamp=datetime.utcnow()
    )


# ==================== ENDPOINT 3: Ask Question ====================

@router.post("/chat/question", response_model=QuestionResponse, tags=["Q&A"])
async def ask_question(
    request: Request,
    question_request: QuestionRequest,
    db: Session = Depends(get_db_session)
):
    """Ask a question about PDF content."""
    logger.info(f"Question asked for PDF {question_request.file_id}: {question_request.question[:50]}...")

    # Lazy imports
    from agents import ContextGuardAgent, QAAgent

    pdf = db.query(PDF).filter(PDF.id == question_request.file_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    topics = db.query(Topic).filter(Topic.pdf_id == question_request.file_id).all()
    topic_list = [{'name': t.topic_name, 'description': t.description} for t in topics]

    gemini_client = getattr(request.app.state, 'gemini_client', None)
    vector_store = getattr(request.app.state, 'vector_store', None)
    if not gemini_client or not vector_store:
        raise HTTPException(status_code=503, detail="Service not initialized")

    context_guard = ContextGuardAgent(gemini_client)
    guard_result = context_guard.process(topic_list, question_request.question)
    if guard_result.success and not guard_result.data.get('allow_query', True):
        raise HTTPException(
            status_code=400,
            detail=guard_result.data.get('user_message', 'Question not relevant to PDF content')
        )

    qa_agent = QAAgent(gemini_client, vector_store)
    answer_result = qa_agent.process(
        pdf_id=str(question_request.file_id),
        question=question_request.question,
        user_language_level=question_request.user_language_level,
        target_language=question_request.language
    )
    if not answer_result.success:
        raise HTTPException(status_code=500, detail="Failed to generate answer")
    answer_data = answer_result.data

    session_id = uuid.uuid4()
    qa_session = QASession(
        id=session_id,
        pdf_id=question_request.file_id,
        user_id=question_request.user_id,
        question=question_request.question,
        answer=answer_data.get('answer', ''),
        source_section=answer_data.get('source_section'),
        source_chunks=answer_data.get('source_chunks', []),
        page_number=answer_data.get('page_number'),
        confidence_score=answer_data.get('confidence', 0.0),
        language_level=question_request.user_language_level
    )
    db.add(qa_session)
    db.commit()

    return QuestionResponse(
        answer=answer_data.get('answer', ''),
        source_section=answer_data.get('source_section', 'PDF Content'),
        page_number=answer_data.get('page_number'),
        confidence_score=answer_data.get('confidence', 0.0),
        source_chunks=[
            SourceChunk(
                text=chunk.get('text', ''),
                page=chunk.get('page', 0),
                confidence=chunk.get('confidence', 0.0)
            )
            for chunk in answer_data.get('source_chunks', [])
        ],
        language_level=question_request.user_language_level,
        session_id=session_id
    )


# ==================== ENDPOINT 4: Get PDF Metadata ====================

@router.get("/pdfs/{file_id}", tags=["PDF Management"])
async def get_pdf_metadata(
    file_id: uuid.UUID,
    db: Session = Depends(get_db_session)
):
    """Get PDF metadata and status."""
    pdf = db.query(PDF).filter(PDF.id == file_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    topics_count = db.query(Topic).filter(Topic.pdf_id == file_id).count()
    sessions_count = db.query(QASession).filter(QASession.pdf_id == file_id).count()

    return {
        'file_id': str(pdf.id),
        'filename': pdf.filename,
        'upload_date': pdf.upload_date.isoformat(),
        'file_size': pdf.file_size,
        'total_pages': pdf.total_pages,
        'status': pdf.status,
        'language': pdf.language,
        'detected_topic': pdf.detected_topic,
        'metadata': pdf.pdf_metadata,
        'topics_count': topics_count,
        'sessions_count': sessions_count
    }


# ==================== ENDPOINT 5: Language Feedback ====================

@router.post("/language-feedback", response_model=LanguageFeedbackResponse, tags=["Language Coaching"])
async def get_language_feedback(
    request: Request,
    feedback_request: LanguageFeedbackRequest,
    db: Session = Depends(get_db_session)
):
    """Get personalized language feedback on user's output."""
    from agents import LanguageCoachAgent

    gemini_client = getattr(request.app.state, 'gemini_client', None)
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    coach = LanguageCoachAgent(gemini_client)
    feedback_result = coach.process(
        user_output=feedback_request.user_output,
        correct_form=feedback_request.correct_form,
        context=feedback_request.context,
        user_language_level="Intermediate"
    )
    if not feedback_result.success:
        raise HTTPException(status_code=500, detail="Failed to generate feedback")
    feedback_data = feedback_result.data

    mistakes_logged = 0
    for mistake in feedback_data.get('mistakes_found', []):
        mistake_record = LanguageMistake(
            pdf_id=feedback_request.pdf_id,
            user_id=feedback_request.user_id,
            mistake_text=mistake.get('mistake_text', ''),
            correction=mistake.get('correction', ''),
            mistake_type=mistake.get('mistake_type', 'grammar'),
            context=feedback_request.context,
            confidence_score=feedback_data.get('confidence', 0.0),
            feedback=mistake.get('explanation', '')
        )
        db.add(mistake_record)
        mistakes_logged += 1
    db.commit()

    vocab_suggestions = [
        VocabularySuggestion(
            original=vs.get('original', ''),
            suggestions=vs.get('suggestions', []),
            explanation=vs.get('explanation', '')
        )
        for vs in feedback_data.get('vocabulary_suggestions', [])
    ]

    return LanguageFeedbackResponse(
        grammar_feedback=feedback_data.get('grammar_feedback', ''),
        vocabulary_suggestions=vocab_suggestions,
        fluency_notes=feedback_data.get('fluency_notes', ''),
        confidence=feedback_data.get('confidence', 0.0),
        encouragement=feedback_data.get('encouragement', 'Keep practicing!'),
        mistakes_logged=mistakes_logged
    )


# ==================== ENDPOINT 6: Translate Content ====================

@router.post("/translate", response_model=TranslationResponse, tags=["Translation"])
async def translate_content(
    request: Request,
    translation_request: TranslationRequest,
    db: Session = Depends(get_db_session)
):
    """Translate PDF content to target language."""
    from agents import TranslatorAgent

    pdf = db.query(PDF).filter(PDF.id == translation_request.file_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    topics = db.query(Topic).filter(Topic.pdf_id == translation_request.file_id).all()
    topic_list = [
        {
            'name': t.topic_name,
            'description': t.description,
            'vocabulary': t.vocabulary
        }
        for t in topics[:10]
    ]

    gemini_client = getattr(request.app.state, 'gemini_client', None)
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    translator = TranslatorAgent(gemini_client)
    translation_result = translator.process(
        content="",
        topics=topic_list,
        source_language=pdf.language,
        target_language=translation_request.target_language,
        include_pronunciation=translation_request.include_pronunciation
    )
    if not translation_result.success:
        raise HTTPException(status_code=500, detail="Translation failed")
    translation_data = translation_result.data

    translation_id = uuid.uuid4()
    translation_record = Translation(
        id=translation_id,
        pdf_id=translation_request.file_id,
        source_language=pdf.language,
        target_language=translation_request.target_language,
        translated_topics=translation_data.get('translated_topics', []),
        translated_content={}
    )
    db.add(translation_record)
    db.commit()

    translated_topics = [
        TranslatedTopic(
            original_name=t.get('original_name', ''),
            translated_name=t.get('translated_name', ''),
            original_description=t.get('original_description', ''),
            translated_description=t.get('translated_description', ''),
            pronunciation=t.get('pronunciation')
        )
        for t in translation_data.get('translated_topics', [])
    ]

    return TranslationResponse(
        translation_id=translation_id,
        source_language=pdf.language,
        target_language=translation_request.target_language,
        translated_topics=translated_topics,
        download_url=None,
        translation_timestamp=datetime.utcnow()
    )


# ==================== ENDPOINT 7: Analyze Mistakes ====================

@router.post("/language-coach/analyze", tags=["Language Coaching"])
async def analyze_mistakes(
    request: Request,
    user_id: uuid.UUID = Query(...),
    pdf_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Analyze user's language mistakes and provide insights."""
    from agents import LanguageCoachAgent

    gemini_client = getattr(request.app.state, 'gemini_client', None)
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    qa_query = db.query(QASession).filter(QASession.user_id == user_id)
    mistakes_query = db.query(LanguageMistake).filter(LanguageMistake.user_id == user_id)
    if pdf_id:
        qa_query = qa_query.filter(QASession.pdf_id == pdf_id)
        mistakes_query = mistakes_query.filter(LanguageMistake.pdf_id == pdf_id)
    qa_sessions = qa_query.all()
    mistakes = mistakes_query.all()

    qa_data = [
        {
            'question': s.question,
            'answer': s.answer,
            'confidence_score': s.confidence_score
        }
        for s in qa_sessions
    ]
    mistake_data = [
        {
            'mistake_text': m.mistake_text,
            'correction': m.correction,
            'mistake_type': m.mistake_type,
            'context': m.context
        }
        for m in mistakes
    ]

    coach = LanguageCoachAgent(gemini_client)
    analysis = coach.analyze_mistakes(qa_data, mistake_data)

    return {
        'user_id': str(user_id),
        'analysis': analysis,
        'total_sessions': len(qa_sessions),
        'total_mistakes': len(mistakes),
        'accuracy_percentage': analysis.get('accuracy_percentage', 0.0)
    }


# ==================== ENDPOINT 8: Generate Learning Report ====================

@router.get("/reports/{file_id}", response_model=LearningReportResponse, tags=["Reports"])
async def generate_learning_report(
    request: Request,
    file_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db_session)
):
    """Generate comprehensive learning report for a user."""
    from agents import FlagReporterAgent

    gemini_client = getattr(request.app.state, 'gemini_client', None)
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    qa_sessions = db.query(QASession).filter(
        QASession.pdf_id == file_id,
        QASession.user_id == user_id
    ).all()
    mistakes = db.query(LanguageMistake).filter(
        LanguageMistake.pdf_id == file_id,
        LanguageMistake.user_id == user_id
    ).all()

    session_data = {
        'qa_sessions': [
            {
                'question': s.question,
                'answer': s.answer,
                'confidence_score': s.confidence_score
            }
            for s in qa_sessions
        ],
        'mistakes': [
            {
                'mistake_text': m.mistake_text,
                'correction': m.correction,
                'mistake_type': m.mistake_type,
                'context': m.context
            }
            for m in mistakes
        ]
    }

    reporter = FlagReporterAgent(gemini_client)
    report_result = reporter.process(
        user_id=str(user_id),
        pdf_id=str(file_id),
        session_data=session_data
    )
    if not report_result.success:
        raise HTTPException(status_code=500, detail="Report generation failed")
    report_data = report_result.data['report_data']

    report_id = uuid.uuid4()
    report_record = LearningReport(
        id=report_id,
        user_id=user_id,
        pdf_id=file_id,
        report_data=report_data,
        accuracy_score=report_data.get('accuracy_percentage', 0.0),
        learning_gaps=report_data.get('learning_gaps', []),
        recommendations=report_data.get('recommendations', [])
    )
    db.add(report_record)
    db.commit()

    learning_gaps = [
        LearningGap(
            topic=gap.get('topic', ''),
            description=gap.get('description', ''),
            severity=gap.get('severity', 'Low'),
            recommendations=gap.get('recommendations', [])
        )
        for gap in report_data.get('learning_gaps', [])
    ]

    return LearningReportResponse(
        report_id=report_id,
        user_id=user_id,
        summary=report_data.get('summary', ''),
        learning_gaps=learning_gaps,
        accuracy_percentage=report_data.get('accuracy_percentage', 0.0),
        total_sessions=report_data.get('total_sessions', 0),
        total_mistakes=report_data.get('total_mistakes', 0),
        most_common_mistake_type=report_data.get('most_common_mistake_type', 'none'),
        recommendations=report_data.get('recommendations', []),
        generated_at=datetime.utcnow(),
        download_url=None
    )


# ==================== ENDPOINT 9: Get Q&A Sessions ====================

@router.get("/pdfs/{file_id}/sessions", tags=["Q&A"])
async def get_qa_sessions(
    file_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db_session)
):
    """Get Q&A session history for a PDF."""
    query = db.query(QASession).filter(QASession.pdf_id == file_id)
    if user_id:
        query = query.filter(QASession.user_id == user_id)
    total = query.count()
    sessions = query.order_by(desc(QASession.timestamp)).limit(limit).offset(offset).all()

    return {
        'file_id': str(file_id),
        'total_sessions': total,
        'limit': limit,
        'offset': offset,
        'sessions': [
            {
                'id': str(s.id),
                'question': s.question,
                'answer': s.answer,
                'source_section': s.source_section,
                'page_number': s.page_number,
                'confidence_score': s.confidence_score,
                'language_level': s.language_level,
                'timestamp': s.timestamp.isoformat()
            }
            for s in sessions
        ]
    }


# ==================== ENDPOINT 10: Create User ====================

@router.post("/users", response_model=UserResponse, tags=["User Management"])
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new user account."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        email=user_data.email,
        language_focus=user_data.language_focus,
        proficiency_level=user_data.proficiency_level
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        language_focus=user.language_focus,
        proficiency_level=user.proficiency_level,
        created_at=user.created_at
    )
