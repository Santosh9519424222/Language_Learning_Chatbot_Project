"""
Helper Utilities
Common helper functions for the platform

Author: Santosh Yadav
Date: November 2025
"""

import uuid
import re
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

logger = logging.getLogger(__name__)


# ==================== ID & TIMESTAMP UTILITIES ====================

def generate_unique_id() -> str:
    """
    Generate a unique UUID string.

    Returns:
        str: UUID string
    """
    return str(uuid.uuid4())


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime to ISO 8601 format with Z suffix.

    Args:
        dt: Datetime object (defaults to now if None)

    Returns:
        str: ISO formatted timestamp
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + 'Z'


# ==================== TEXT PROCESSING UTILITIES ====================

def clean_text(text: str, remove_extra_whitespace: bool = True) -> str:
    """
    Clean and normalize text.

    Args:
        text: Text to clean
        remove_extra_whitespace: Whether to remove extra whitespace

    Returns:
        str: Cleaned text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove extra whitespace
    if remove_extra_whitespace:
        text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Size of each chunk
        overlap: Overlap between chunks

    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap if end < len(text) else len(text)

    return chunks


def detect_language(text: str) -> str:
    """
    Detect language of text (simple heuristic).

    Args:
        text: Text to analyze

    Returns:
        str: Language name
    """
    try:
        from langdetect import detect, LangDetectException

        if not text or len(text.strip()) < 50:
            return "Unknown"

        lang_code = detect(text)

        # Map common codes to names
        lang_map = {
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

        return lang_map.get(lang_code, lang_code.upper())

    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "Unknown"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe storage.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Truncate if too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename or 'untitled'


# ==================== VALIDATION UTILITIES ====================

def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address

    Returns:
        bool: True if valid
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def calculate_accuracy(correct: int, total: int) -> float:
    """
    Calculate accuracy percentage.

    Args:
        correct: Number of correct answers
        total: Total number of attempts

    Returns:
        float: Accuracy percentage (0-100)
    """
    if total == 0:
        return 0.0

    accuracy = (correct / total) * 100
    return round(accuracy, 2)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# ==================== EXPORT UTILITIES ====================

def export_to_csv(
    data: List[Dict[str, Any]],
    output_path: str,
    fieldnames: Optional[List[str]] = None
) -> str:
    """
    Export data to CSV file.

    Args:
        data: List of dictionaries to export
        output_path: Output file path
        fieldnames: Optional list of field names (inferred if None)

    Returns:
        str: Path to created CSV file
    """
    logger.info(f"Exporting {len(data)} records to CSV: {output_path}")

    try:
        if not data:
            logger.warning("No data to export")
            return output_path

        # Infer fieldnames if not provided
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                # Only write fields that exist in fieldnames
                filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                writer.writerow(filtered_row)

        logger.info(f"CSV export completed: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise


def save_report_pdf(
    report_data: Dict[str, Any],
    output_path: str,
    title: str = "Learning Report"
) -> str:
    """
    Generate PDF report from report data.

    Args:
        report_data: Report data dictionary
        output_path: Output PDF path
        title: Report title

    Returns:
        str: Path to created PDF
    """
    logger.info(f"Generating PDF report: {output_path}")

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Container for elements
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            spaceBefore=12
        )

        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))

        # Add generation date
        date_text = f"Generated: {datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))

        # Add summary
        if 'summary' in report_data:
            story.append(Paragraph("Summary", heading_style))
            story.append(Paragraph(report_data['summary'], styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        # Add accuracy
        if 'accuracy_percentage' in report_data:
            accuracy_text = f"<b>Overall Accuracy:</b> {report_data['accuracy_percentage']:.1f}%"
            story.append(Paragraph(accuracy_text, styles['Normal']))
            story.append(Spacer(1, 0.2*inch))

        # Add statistics table
        if 'total_sessions' in report_data or 'total_mistakes' in report_data:
            story.append(Paragraph("Statistics", heading_style))

            stats_data = [
                ['Metric', 'Value'],
                ['Total Sessions', str(report_data.get('total_sessions', 0))],
                ['Total Mistakes', str(report_data.get('total_mistakes', 0))],
                ['Most Common Mistake Type', report_data.get('most_common_mistake_type', 'N/A').title()]
            ]

            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(stats_table)
            story.append(Spacer(1, 0.3*inch))

        # Add learning gaps
        if 'learning_gaps' in report_data and report_data['learning_gaps']:
            story.append(Paragraph("Learning Gaps", heading_style))

            for i, gap in enumerate(report_data['learning_gaps'][:5], 1):
                gap_text = f"<b>{i}. {gap.get('topic', 'Unknown')} ({gap.get('severity', 'Low')} Priority)</b><br/>"
                gap_text += f"{gap.get('description', '')}"
                story.append(Paragraph(gap_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

        # Add recommendations
        if 'recommendations' in report_data and report_data['recommendations']:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Recommendations", heading_style))

            for i, rec in enumerate(report_data['recommendations'][:5], 1):
                if isinstance(rec, dict):
                    rec_text = f"{i}. <b>{rec.get('action', '')}</b><br/>{rec.get('reason', '')}"
                else:
                    rec_text = f"{i}. {rec}"
                story.append(Paragraph(rec_text, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))

        # Add strengths
        if 'strengths' in report_data and report_data['strengths']:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Your Strengths", heading_style))

            for strength in report_data['strengths']:
                story.append(Paragraph(f"✓ {strength}", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))

        # Add motivation message
        if 'motivation_message' in report_data:
            story.append(Spacer(1, 0.3*inch))
            motivation_style = ParagraphStyle(
                'Motivation',
                parent=styles['Normal'],
                fontSize=14,
                textColor=colors.HexColor('#34a853'),
                alignment=TA_CENTER,
                spaceAfter=12
            )
            story.append(Paragraph(report_data['motivation_message'], motivation_style))

        # Build PDF
        doc.build(story)

        logger.info(f"PDF report generated: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise


def export_mistakes_to_csv(
    mistakes: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Export mistakes to CSV with specific formatting.

    Args:
        mistakes: List of mistake dictionaries
        output_path: Output CSV path

    Returns:
        str: Path to created CSV
    """
    fieldnames = [
        'mistake_text',
        'correction',
        'mistake_type',
        'context',
        'confidence_score',
        'timestamp'
    ]

    return export_to_csv(mistakes, output_path, fieldnames)


def export_sessions_to_csv(
    sessions: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Export Q&A sessions to CSV.

    Args:
        sessions: List of session dictionaries
        output_path: Output CSV path

    Returns:
        str: Path to created CSV
    """
    fieldnames = [
        'question',
        'answer',
        'confidence_score',
        'language_level',
        'timestamp'
    ]

    return export_to_csv(sessions, output_path, fieldnames)


# ==================== FORMATTING UTILITIES ====================

def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} minutes"
    else:
        return f"{seconds / 3600:.1f} hours"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage.

    Args:
        value: Value (0-100 or 0-1)
        decimals: Number of decimal places

    Returns:
        str: Formatted percentage
    """
    if value > 1:
        # Already in percentage
        return f"{value:.{decimals}f}%"
    else:
        # Convert to percentage
        return f"{value * 100:.{decimals}f}%"


# ==================== PATH UTILITIES ====================

def ensure_directory(path: str) -> str:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        str: Directory path
    """
    os.makedirs(path, exist_ok=True)
    return path


def get_file_extension(filename: str) -> str:
    """
    Get file extension.

    Args:
        filename: Filename

    Returns:
        str: Extension (e.g., ".pdf")
    """
    return os.path.splitext(filename)[1].lower()


def is_valid_pdf(filename: str) -> bool:
    """
    Check if filename has PDF extension.

    Args:
        filename: Filename

    Returns:
        bool: True if PDF extension
    """
    return get_file_extension(filename) == '.pdf'

