"""
Database Models for Multi-Agent PDF Intelligence Platform
SQLAlchemy ORM Models with PostgreSQL or SQLite fallback for demo.

Author: Santosh Yadav
Date: November 2025
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, JSON, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
import os

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/pdf_learning_db"
)
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    UUIDTypeObj = String(36)  # store UUIDs as 36-char strings
    def generate_uuid():
        return str(uuid.uuid4())
else:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        echo=os.getenv("ENVIRONMENT", "development") == "development"
    )
    UUIDTypeObj = PGUUID(as_uuid=True)
    def generate_uuid():
        return uuid.uuid4()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_session() -> Session:
    """
    Dependency for getting database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- Models (only UUID column definitions changed) ----------------
class User(Base):
    """
    User model for storing learner profiles.

    Attributes:
        id: Unique user identifier (UUID)
        username: User's display name
        email: User's email address (unique)
        language_focus: Primary language the user is learning
        known_languages: List of languages user already knows (JSON)
        proficiency_level: Current proficiency (Beginner/Intermediate/Advanced)
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
    """
    __tablename__ = "users"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    username = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    language_focus = Column(String(50), nullable=False)
    known_languages = Column(JSON, default=list)
    proficiency_level = Column(String(20), default="Beginner")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pdfs = relationship("PDF", back_populates="user", cascade="all, delete-orphan")
    qa_sessions = relationship("QASession", back_populates="user", cascade="all, delete-orphan")
    mistakes = relationship("LanguageMistake", back_populates="user", cascade="all, delete-orphan")
    flags = relationship("Flag", back_populates="user", cascade="all, delete-orphan")
    learning_reports = relationship("LearningReport", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, language={self.language_focus})>"


class PDF(Base):
    """
    PDF document model for storing uploaded learning materials.

    Attributes:
        id: Unique PDF identifier (UUID)
        user_id: Foreign key to User
        filename: Original filename
        file_path: Storage path (Cloud Storage URL or local path)
        upload_date: When PDF was uploaded
        file_size: File size in bytes
        total_pages: Number of pages in PDF
        status: Processing status (pending/processing/completed/failed)
        language: Detected language of PDF content
        detected_topic: Main topic/subject of PDF
        pdf_metadata: Additional PDF metadata (JSON)
    """
    __tablename__ = "pdfs"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(UUIDTypeObj, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    total_pages = Column(Integer, nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    language = Column(String(50))
    detected_topic = Column(String(255))
    pdf_metadata = Column(JSON, default=dict)  # renamed from 'metadata' to avoid SQLAlchemy reserved name

    # Relationships
    user = relationship("User", back_populates="pdfs")
    topics = relationship("Topic", back_populates="pdf", cascade="all, delete-orphan")
    qa_sessions = relationship("QASession", back_populates="pdf", cascade="all, delete-orphan")
    mistakes = relationship("LanguageMistake", back_populates="pdf", cascade="all, delete-orphan")
    flags = relationship("Flag", back_populates="pdf", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="pdf", cascade="all, delete-orphan")
    learning_reports = relationship("LearningReport", back_populates="pdf", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_user_upload_date', 'user_id', 'upload_date'),
        Index('idx_status_language', 'status', 'language'),
    )

    def __repr__(self):
        return f"<PDF(id={self.id}, filename={self.filename}, status={self.status})>"


class Topic(Base):
    """
    Extracted topics from PDF documents.

    Attributes:
        id: Unique topic identifier
        pdf_id: Foreign key to PDF
        topic_name: Name of the topic
        description: Detailed description
        page_number: Page where topic appears
        section_hierarchy: Hierarchical structure (JSON)
        difficulty_level: Beginner/Intermediate/Advanced
        vocabulary: Key vocabulary items (JSON list)
        grammar_points: Grammar concepts covered (JSON list)
        created_at: Extraction timestamp
    """
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    page_number = Column(Integer, nullable=False)
    section_hierarchy = Column(JSON, default=dict)
    difficulty_level = Column(String(20), default="Beginner")
    vocabulary = Column(JSON, default=list)
    grammar_points = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    pdf = relationship("PDF", back_populates="topics")

    # Indexes
    __table_args__ = (
        Index('idx_pdf_topic', 'pdf_id', 'topic_name'),
        Index('idx_difficulty', 'difficulty_level'),
    )

    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.topic_name}, difficulty={self.difficulty_level})>"


class QASession(Base):
    """
    Question & Answer session logs for learning tracking.

    Attributes:
        id: Unique session identifier
        pdf_id: Foreign key to PDF
        user_id: Foreign key to User
        question: User's question
        answer: AI-generated answer
        source_section: Section/topic from which answer was derived
        source_chunks: Relevant text chunks used (JSON)
        page_number: Page reference
        confidence_score: AI confidence in answer (0.0-1.0)
        language_level: User's language level at time of query
        timestamp: When question was asked
    """
    __tablename__ = "qa_sessions"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUIDTypeObj, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source_section = Column(String(255))
    source_chunks = Column(JSON, default=list)
    page_number = Column(Integer)
    confidence_score = Column(Float, default=0.0)
    language_level = Column(String(20), default="Beginner")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    pdf = relationship("PDF", back_populates="qa_sessions")
    user = relationship("User", back_populates="qa_sessions")

    # Indexes
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_pdf_timestamp', 'pdf_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<QASession(id={self.id}, confidence={self.confidence_score})>"


class LanguageMistake(Base):
    """
    Language mistakes logged during learning sessions.

    Attributes:
        id: Unique mistake identifier
        pdf_id: Foreign key to PDF (optional, for context)
        user_id: Foreign key to User
        mistake_text: The incorrect text/phrase
        correction: Corrected version
        mistake_type: Type (grammar/vocabulary/pronunciation/fluency)
        context: Surrounding context where mistake occurred
        confidence_score: AI confidence in correction (0.0-1.0)
        feedback: Detailed feedback from Language Coach Agent
        timestamp: When mistake was logged
    """
    __tablename__ = "language_mistakes"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUIDTypeObj, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mistake_text = Column(Text, nullable=False)
    correction = Column(Text, nullable=False)
    mistake_type = Column(String(50), nullable=False, index=True)
    context = Column(Text)
    confidence_score = Column(Float, default=0.0)
    feedback = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    pdf = relationship("PDF", back_populates="mistakes")
    user = relationship("User", back_populates="mistakes")

    # Indexes
    __table_args__ = (
        Index('idx_user_mistake_type', 'user_id', 'mistake_type'),
        Index('idx_lm_user_timestamp', 'user_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<LanguageMistake(id={self.id}, type={self.mistake_type})>"


class Flag(Base):
    """
    User-reported issues with PDF content or AI responses.

    Attributes:
        id: Unique flag identifier
        pdf_id: Foreign key to PDF
        user_id: Foreign key to User
        issue_description: Description of the issue
        category: Issue category (content_error/translation_issue/unclear_explanation/other)
        resolved: Whether issue has been addressed
        resolution_notes: Notes about resolution
        created_at: When flag was created
        resolved_at: When flag was resolved
    """
    __tablename__ = "flags"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUIDTypeObj, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolution_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    pdf = relationship("PDF", back_populates="flags")
    user = relationship("User", back_populates="flags")

    # Indexes
    __table_args__ = (
        Index('idx_resolved_category', 'resolved', 'category'),
    )

    def __repr__(self):
        return f"<Flag(id={self.id}, category={self.category}, resolved={self.resolved})>"


class Translation(Base):
    """
    Translation records for PDF content.

    Attributes:
        id: Unique translation identifier
        pdf_id: Foreign key to PDF
        source_language: Original language
        target_language: Translation language
        translated_topics: Translated topics (JSON)
        translated_content: Full translated content (JSON)
        created_at: Translation timestamp
    """
    __tablename__ = "translations"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_language = Column(String(50), nullable=False)
    target_language = Column(String(50), nullable=False, index=True)
    translated_topics = Column(JSON, default=list)
    translated_content = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    pdf = relationship("PDF", back_populates="translations")

    # Indexes
    __table_args__ = (
        Index('idx_pdf_target_lang', 'pdf_id', 'target_language'),
    )

    def __repr__(self):
        return f"<Translation(id={self.id}, {self.source_language}->{self.target_language})>"


class LearningReport(Base):
    """
    Personalized learning reports generated by Flag Reporter Agent.

    Attributes:
        id: Unique report identifier
        user_id: Foreign key to User
        pdf_id: Foreign key to PDF (optional, for PDF-specific reports)
        report_data: Complete report data (JSON)
        accuracy_score: Overall accuracy percentage (0.0-100.0)
        learning_gaps: Identified learning gaps (JSON list)
        recommendations: Personalized recommendations (JSON list)
        generated_at: Report generation timestamp
    """
    __tablename__ = "learning_reports"

    id = Column(UUIDTypeObj, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(UUIDTypeObj, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    pdf_id = Column(UUIDTypeObj, ForeignKey("pdfs.id", ondelete="CASCADE"), index=True)
    report_data = Column(JSON, default=dict)
    accuracy_score = Column(Float, default=0.0)
    learning_gaps = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="learning_reports")
    pdf = relationship("PDF", back_populates="learning_reports")

    # Indexes
    __table_args__ = (
        Index('idx_user_generated_at', 'user_id', 'generated_at'),
    )

    def __repr__(self):
        return f"<LearningReport(id={self.id}, accuracy={self.accuracy_score})>"


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # Create all tables
    print("Creating database tables...")
    init_db()
    print("✅ Database tables created successfully!")
