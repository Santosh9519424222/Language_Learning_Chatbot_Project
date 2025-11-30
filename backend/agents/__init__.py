"""
Agents Module
All 7 AI Agents for the Multi-Agent PDF Intelligence Platform

Author: Santosh Yadav
Date: November 2025
"""

from .base_agent import BaseAgent, AgentResponse, retry_on_failure
from .pdf_upload_agent import PDFUploadAgent
from .extraction_agent import ExtractionAgent
from .context_guard_agent import ContextGuardAgent
from .qa_agent import QAAgent
from .translator_agent import TranslatorAgent
from .language_coach_agent import LanguageCoachAgent
from .flag_reporter_agent import FlagReporterAgent

__all__ = [
    # Base classes
    'BaseAgent',
    'AgentResponse',
    'retry_on_failure',

    # 7 Specialized Agents
    'PDFUploadAgent',
    'ExtractionAgent',
    'ContextGuardAgent',
    'QAAgent',
    'TranslatorAgent',
    'LanguageCoachAgent',
    'FlagReporterAgent'
]

# Agent registry for easy access
AGENTS = {
    'pdf_upload': PDFUploadAgent,
    'extraction': ExtractionAgent,
    'context_guard': ContextGuardAgent,
    'qa': QAAgent,
    'translator': TranslatorAgent,
    'language_coach': LanguageCoachAgent,
    'flag_reporter': FlagReporterAgent
}


def get_agent_class(agent_name: str):
    """
    Get agent class by name.

    Args:
        agent_name: Name of agent

    Returns:
        Agent class
    """
    return AGENTS.get(agent_name)


def list_agents():
    """List all available agents"""
    return list(AGENTS.keys())

