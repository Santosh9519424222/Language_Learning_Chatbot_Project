"""
Base Agent Class
Abstract base class for all AI agents in the Multi-Agent PDF Intelligence Platform

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypedDict
from functools import wraps
import traceback

logger = logging.getLogger(__name__)


class AgentResponse(TypedDict, total=False):
    """
    Standard response format for all agents.

    Attributes:
        success: Whether the operation was successful
        data: Response data (type depends on agent)
        error: Error message if operation failed
        execution_time: Time taken to execute in seconds
        model: LLM model used (if applicable)
        tokens_used: Approximate tokens used (if applicable)
    """
    success: bool
    data: Dict[str, Any]
    error: Optional[str]
    execution_time: float
    model: Optional[str]
    tokens_used: Optional[int]


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry agent operations on failure.

    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds

    Returns:
        Decorated function that retries on failure
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}: {str(e)}"
                        )
            raise last_error
        return wrapper
    return decorator


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.

    All agents must implement the process() method and follow the
    standard AgentResponse format for consistency.
    """

    def __init__(self, name: str, model: str = "gemini-pro"):
        """
        Initialize the base agent.

        Args:
            name: Agent name (e.g., 'pdf_upload', 'qa', etc.)
            model: LLM model to use
        """
        self.name = name
        self.model = model
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @abstractmethod
    def process(self, **kwargs) -> AgentResponse:
        """
        Process input and return structured response.

        Must be implemented by all subclasses.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            AgentResponse: Standard response object
        """
        pass

    def _create_response(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time: float = 0.0,
        tokens_used: Optional[int] = None
    ) -> AgentResponse:
        """
        Create a standardized response object.

        Args:
            success: Whether operation was successful
            data: Response data
            error: Error message if failed
            execution_time: Execution time in seconds
            tokens_used: Approximate tokens used

        Returns:
            AgentResponse: Formatted response
        """
        return AgentResponse(
            success=success,
            data=data or {},
            error=error,
            execution_time=execution_time,
            model=self.model,
            tokens_used=tokens_used
        )

    def _safe_execute(
        self,
        func: callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Safely execute a function with error handling and timeout.

        Args:
            func: Function to execute
            timeout: Maximum execution time in seconds
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Dict with result or error
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'error': None
            }
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(f"Error in {func.__name__}: {error_msg}")

            return {
                'success': False,
                'result': None,
                'execution_time': execution_time,
                'error': error_msg
            }

    def validate_inputs(self, required_fields: list, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that required fields are present in input data.

        Args:
            required_fields: List of required field names
            data: Input data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_fields = [f for f in required_fields if f not in data or data[f] is None]

        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            return False, error_msg

        return True, None

    def log_execution(self, operation: str, status: str, details: Optional[str] = None):
        """
        Log agent execution for monitoring and debugging.

        Args:
            operation: Operation name
            status: Success/failure status
            details: Additional details
        """
        log_level = logging.INFO if status == "success" else logging.WARNING
        message = f"[{self.name}] {operation}: {status}"
        if details:
            message += f" - {details}"
        self.logger.log(log_level, message)


# Specialized Base Classes for Different Agent Types

class LLMAgent(BaseAgent):
    """
    Base class for agents that use LLM (Large Language Model) APIs.
    """

    def __init__(self, gemini_client, name: str, model: str = "gemini-pro"):
        """
        Initialize LLM agent with Gemini client.

        Args:
            gemini_client: Initialized GeminiClient instance
            name: Agent name
            model: LLM model
        """
        super().__init__(name, model)
        self.gemini_client = gemini_client

    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> tuple[bool, Optional[str]]:
        """
        Generate text using Gemini API.

        Args:
            prompt: Input prompt
            temperature: Creativity level (0-1)
            max_tokens: Maximum output tokens

        Returns:
            Tuple of (success, generated_text or error_message)
        """
        try:
            # Call the correct Gemini client method
            response = self.gemini_client.generate_content(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return True, response
        except Exception as e:
            error_msg = f"Text generation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def parse_json_response(self, text: str) -> tuple[bool, Optional[dict]]:
        """
        Parse JSON from LLM response with fallback.

        Args:
            text: LLM response text

        Returns:
            Tuple of (success, parsed_dict or None)
        """
        import json
        try:
            # Try to find JSON in response
            json_start = text.find('{')
            json_end = text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = text[json_start:json_end]
                parsed = json.loads(json_str)
                return True, parsed

            return False, None
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parsing failed: {str(e)}")
            return False, None


class StorageAgent(BaseAgent):
    """
    Base class for agents that access vector storage.
    """

    def __init__(self, vector_store, name: str, model: str = "gemini-pro"):
        """
        Initialize storage agent with vector store.

        Args:
            vector_store: Initialized ChromaVectorStore instance (can be None)
            name: Agent name
            model: LLM model
        """
        super().__init__(name, model)
        self.vector_store = vector_store

    def search_similar(self, query: str, pdf_id: str, top_k: int = 5) -> tuple[bool, Optional[list]]:
        """
        Search for similar documents in vector store.

        Args:
            query: Search query
            pdf_id: PDF identifier
            top_k: Number of results to return

        Returns:
            Tuple of (success, results or None)
        """
        if not self.vector_store:
            self.logger.warning("Vector store not initialized; cannot perform semantic search")
            return False, None

        try:
            results = self.vector_store.retrieve_relevant_chunks(
                query=query,
                pdf_id=pdf_id,
                top_k=top_k
            )
            return True, results
        except Exception as e:
            error_msg = f"Vector search failed: {str(e)}"
            self.logger.error(error_msg)
            return False, None

