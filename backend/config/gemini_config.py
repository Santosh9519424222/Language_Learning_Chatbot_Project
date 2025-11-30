"""
Google Gemini API Configuration and Client
Handles Gemini API interactions with rate limiting

Author: Santosh Yadav
Date: November 2025
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai  # type: ignore
except Exception as e:  # pragma: no cover
    genai = None
    logger.warning("google.generativeai not installed; running in degraded mode")


class GeminiClient:
    """
    Google Gemini API client with rate limiting and error handling.
    FREE tier: 60 requests per minute
    """

    # Rate limiting constants (FREE tier)
    MAX_REQUESTS_PER_MINUTE = 60
    RATE_LIMIT_WINDOW = 60  # seconds

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        """
        Initialize Gemini API client.

        Args:
            api_key: Gemini API key (from env if not provided)
            model_name: Gemini model name
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        if genai:
            try:
                # Configure Gemini
                genai.configure(api_key=self.api_key)

                # Initialize model
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    safety_settings={
                        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
                    }
                )

                # Rate limiting tracking
                self._request_times: List[float] = []
                self._lock = threading.Lock()

                logger.info(f"✅ Gemini client initialized with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini client: {e}")
                self.model = None
        else:
            self.model = None

    def _check_rate_limit(self) -> bool:
        """
        Check if request can be made within rate limits.

        Returns:
            bool: True if request can proceed
        """
        with self._lock:
            current_time = time.time()

            # Remove requests older than the window
            self._request_times = [
                t for t in self._request_times
                if current_time - t < self.RATE_LIMIT_WINDOW
            ]

            # Check if we're within limits
            if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
                logger.warning("Rate limit reached. Waiting...")
                return False

            # Record this request
            self._request_times.append(current_time)
            return True

    def _wait_for_rate_limit(self, max_wait: int = 65):
        """
        Wait until rate limit allows request.

        Args:
            max_wait: Maximum seconds to wait
        """
        start_wait = time.time()

        while not self._check_rate_limit():
            if time.time() - start_wait > max_wait:
                raise Exception("Rate limit wait timeout exceeded")
            time.sleep(1)

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        wait_on_rate_limit: bool = True
    ) -> str:
        """
        Generate content using Gemini API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            wait_on_rate_limit: Whether to wait if rate limited

        Returns:
            str: Generated content
        """
        try:
            if not self.model:
                logger.warning("Gemini model not available; cannot generate content")
                return ""

            # Check/wait for rate limit
            if wait_on_rate_limit:
                self._wait_for_rate_limit()
            elif not self._check_rate_limit():
                raise Exception("Rate limit exceeded")

            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )

            # Extract text
            if response and response.text:
                logger.debug(f"Generated {len(response.text)} characters")
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return ""

        except Exception as e:
            logger.error(f"Gemini generation error: {e}", exc_info=True)
            raise

    def generate_content_with_context(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content with system prompt and context.

        Args:
            system_prompt: System/role prompt
            user_prompt: User's query/prompt
            context: Optional context information
            temperature: Sampling temperature

        Returns:
            str: Generated content
        """
        # Construct full prompt
        full_prompt = f"{system_prompt}\n\n"

        if context:
            full_prompt += f"CONTEXT:\n{context}\n\n"

        full_prompt += f"USER QUERY:\n{user_prompt}"

        return self.generate_content(full_prompt, temperature=temperature)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        Chat-based interaction with message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature

        Returns:
            str: Assistant response
        """
        try:
            if not self.model:
                logger.warning("Gemini model not available; cannot chat")
                return ""

            # Start chat session
            chat = self.model.start_chat(history=[])

            # Send messages
            for msg in messages[:-1]:  # All except last
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])

            # Get response for last message
            last_message = messages[-1]['content']
            response = chat.send_message(
                last_message,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )

            return response.text if response and response.text else ""

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            int: Token count
        """
        try:
            if not self.model:
                logger.warning("Gemini model not available; cannot count tokens")
                return 0

            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4

    def get_quota_status(self) -> Dict[str, Any]:
        """
        Get current API quota status.

        Returns:
            dict: Quota information
        """
        with self._lock:
            current_time = time.time()

            # Clean old requests
            self._request_times = [
                t for t in self._request_times
                if current_time - t < self.RATE_LIMIT_WINDOW
            ]

            requests_used = len(self._request_times)
            requests_remaining = self.MAX_REQUESTS_PER_MINUTE - requests_used

            # Calculate reset time
            if self._request_times:
                oldest_request = min(self._request_times)
                reset_time = datetime.fromtimestamp(
                    oldest_request + self.RATE_LIMIT_WINDOW
                )
            else:
                reset_time = datetime.now()

            return {
                'available': True,
                'requests_used': requests_used,
                'requests_remaining': requests_remaining,
                'max_requests_per_minute': self.MAX_REQUESTS_PER_MINUTE,
                'reset_time': reset_time.isoformat(),
                'model': self.model_name
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Check Gemini API health.

        Returns:
            dict: Health status
        """
        try:
            # Simple test generation
            test_prompt = "Say 'OK' if you're working."
            response = self.generate_content(test_prompt, max_tokens=10)

            return {
                'status': 'healthy',
                'model': self.model_name,
                'test_response': response[:50],
                'quota': self.get_quota_status()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'model': self.model_name
            }


# Module-level convenience functions
_gemini_client_instance: Optional[GeminiClient] = None


def get_gemini_client(model_name: str = "gemini-pro") -> GeminiClient:
    """
    Get or create Gemini client singleton.

    Args:
        model_name: Gemini model name

    Returns:
        GeminiClient: Gemini client instance
    """
    global _gemini_client_instance

    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient(model_name=model_name)

    return _gemini_client_instance
