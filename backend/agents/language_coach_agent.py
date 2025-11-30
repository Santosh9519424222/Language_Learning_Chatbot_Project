"""
Language Coach Agent
Provides personalized language feedback and corrections

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import LANGUAGE_COACH_AGENT_PROMPT
from config.gemini_config import GeminiClient

logger = logging.getLogger(__name__)


class LanguageCoachAgent(BaseAgent):
    """
    Agent responsible for providing personalized language feedback.
    Analyzes mistakes, provides corrections, and suggests improvements.
    This is the core agent for the language learning functionality.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Language Coach Agent.

        Args:
            gemini_client: Gemini API client instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="LanguageCoachAgent",
            system_prompt=LANGUAGE_COACH_AGENT_PROMPT,
            temperature=0.6  # Balance between creativity and consistency
        )

    def process(
        self,
        user_output: str,
        correct_form: str = None,
        context: str = None,
        user_language_level: str = "Intermediate"
    ) -> AgentResponse:
        """
        Analyze user's language output and provide feedback.

        Args:
            user_output: User's text to analyze
            correct_form: Optional correct version
            context: Optional context
            user_language_level: User's proficiency level

        Returns:
            AgentResponse: Detailed feedback and corrections
        """
        start_time = time.time()

        try:
            self.logger.info(f"Analyzing language output: '{user_output[:50]}...'")

            # Generate comprehensive feedback
            feedback_data = self._analyze_and_provide_feedback(
                user_output=user_output,
                correct_form=correct_form,
                context=context,
                language_level=user_language_level
            )

            duration = time.time() - start_time
            self.log_performance('language_coaching', duration, True)

            self.logger.info(
                f"Language feedback generated",
                extra={
                    'mistakes_found': len(feedback_data.get('mistakes_found', [])),
                    'confidence': feedback_data.get('confidence', 0.0),
                    'duration': duration
                }
            )

            return AgentResponse(
                success=True,
                data=feedback_data,
                agent_name=self.agent_name,
                duration=duration
            )

        except Exception as e:
            self.logger.error(f"Language coaching failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def _analyze_and_provide_feedback(
        self,
        user_output: str,
        correct_form: str,
        context: str,
        language_level: str
    ) -> Dict[str, Any]:
        """
        Use AI to analyze and provide detailed feedback.

        Args:
            user_output: User's text
            correct_form: Correct version (optional)
            context: Context (optional)
            language_level: User's level

        Returns:
            dict: Comprehensive feedback
        """
        prompt = f"""
User's Language Level: {language_level}
User's Output: {user_output}
"""

        if correct_form:
            prompt += f"\nCorrect Form: {correct_form}"

        if context:
            prompt += f"\nContext: {context}"

        prompt += """

Analyze the user's language output and provide:
1. Grammar feedback with corrections
2. Vocabulary suggestions
3. Fluency notes
4. Specific mistakes with explanations
5. Encouragement and praise for what they did well
6. Practice recommendations
"""

        try:
            response = self.generate_response(prompt)
            feedback = self.parse_json_response(response)

            # Ensure all required fields are present
            required_fields = [
                'grammar_feedback',
                'vocabulary_suggestions',
                'fluency_notes',
                'mistakes_found',
                'confidence',
                'overall_assessment',
                'encouragement',
                'practice_recommendations',
                'progress_notes'
            ]

            for field in required_fields:
                if field not in feedback:
                    feedback[field] = self._get_default_value(field)

            return feedback

        except Exception as e:
            self.logger.error(f"Feedback generation failed: {e}")
            raise

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            'grammar_feedback': 'No specific grammar issues detected.',
            'vocabulary_suggestions': [],
            'fluency_notes': 'Natural expression.',
            'mistakes_found': [],
            'confidence': 0.5,
            'overall_assessment': 'Good attempt!',
            'encouragement': 'Keep practicing!',
            'practice_recommendations': ['Continue practicing regularly'],
            'progress_notes': 'You\'re making progress!'
        }
        return defaults.get(field, '')

    def analyze_mistakes(
        self,
        qa_sessions: List[Dict[str, Any]],
        mistakes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns in user's mistakes over time.

        Args:
            qa_sessions: List of Q&A sessions
            mistakes: List of logged mistakes

        Returns:
            dict: Analysis of mistake patterns
        """
        try:
            # Count mistake types
            mistake_types = {}
            for mistake in mistakes:
                mtype = mistake.get('mistake_type', 'unknown')
                mistake_types[mtype] = mistake_types.get(mtype, 0) + 1

            # Calculate accuracy
            total_sessions = len(qa_sessions)
            total_mistakes = len(mistakes)

            if total_sessions > 0:
                accuracy = max(0, 100 - (total_mistakes / total_sessions * 10))
            else:
                accuracy = 100

            return {
                'total_sessions': total_sessions,
                'total_mistakes': total_mistakes,
                'mistake_types': mistake_types,
                'accuracy_percentage': round(accuracy, 2),
                'most_common_type': max(mistake_types.items(), key=lambda x: x[1])[0] if mistake_types else 'none'
            }

        except Exception as e:
            self.logger.error(f"Mistake analysis failed: {e}")
            return {
                'total_sessions': 0,
                'total_mistakes': 0,
                'mistake_types': {},
                'accuracy_percentage': 0.0,
                'most_common_type': 'unknown'
            }

    def provide_feedback(self, user_output: str, correct_form: str) -> Dict[str, Any]:
        """
        Simplified feedback method.

        Args:
            user_output: User's text
            correct_form: Correct version

        Returns:
            dict: Feedback
        """
        result = self.process(user_output, correct_form)
        if result.success:
            return result.data
        else:
            return {'error': result.error}

    def detect_mistake_type(self, mistake_text: str, correction: str) -> str:
        """
        Detect the type of mistake.

        Args:
            mistake_text: Incorrect text
            correction: Correct text

        Returns:
            str: Mistake type (grammar/vocabulary/syntax/pronunciation)
        """
        prompt = f"""
Incorrect: {mistake_text}
Correct: {correction}

What type of mistake is this? (grammar, vocabulary, syntax, pronunciation, or fluency)
Answer with just the type.
"""

        try:
            response = self.generate_response(prompt, temperature=0.3)
            mistake_type = response.strip().lower()

            valid_types = ['grammar', 'vocabulary', 'syntax', 'pronunciation', 'fluency']
            if mistake_type in valid_types:
                return mistake_type
            else:
                return 'grammar'  # Default

        except Exception as e:
            self.logger.warning(f"Mistake type detection failed: {e}")
            return 'grammar'

    def calculate_accuracy(self, qa_sessions: List[Dict[str, Any]]) -> float:
        """
        Calculate user's overall accuracy percentage.

        Args:
            qa_sessions: List of Q&A sessions with confidence scores

        Returns:
            float: Accuracy percentage (0-100)
        """
        if not qa_sessions:
            return 0.0

        total_confidence = sum(
            session.get('confidence_score', 0.5)
            for session in qa_sessions
        )

        avg_confidence = total_confidence / len(qa_sessions)
        accuracy = avg_confidence * 100

        return round(accuracy, 2)

    def generate_recommendations(self, learning_gaps: List[Dict[str, Any]]) -> List[str]:
        """
        Generate personalized learning recommendations.

        Args:
            learning_gaps: Identified learning gaps

        Returns:
            List[str]: Recommendations
        """
        if not learning_gaps:
            return ["Continue practicing regularly to maintain your level"]

        recommendations = []

        for gap in learning_gaps[:5]:  # Top 5 gaps
            topic = gap.get('topic', 'Unknown topic')
            severity = gap.get('severity', 'Medium')

            if severity == 'High':
                recommendations.append(f"📚 Priority: Review {topic} - this needs immediate attention")
            elif severity == 'Medium':
                recommendations.append(f"📖 Important: Practice {topic} exercises")
            else:
                recommendations.append(f"📝 Suggestion: Reinforce {topic} when you have time")

        return recommendations

    def create_personalized_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a personalized learning report.

        Args:
            session_data: User's session data

        Returns:
            dict: Personalized report
        """
        # This method ties into the Flag Reporter Agent
        # Provides data for comprehensive reports

        return {
            'summary': session_data.get('summary', ''),
            'strengths': session_data.get('strengths', []),
            'areas_for_improvement': session_data.get('improvements_needed', []),
            'recommended_actions': self.generate_recommendations(
                session_data.get('learning_gaps', [])
            ),
            'motivation': 'You\'re doing great! Keep up the excellent work!'
        }

