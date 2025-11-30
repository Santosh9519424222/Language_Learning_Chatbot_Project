"""
Flag Reporter Agent
Generates personalized learning reports with gap analysis

Author: Santosh Yadav
Date: November 2025
"""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from agents.base_agent import BaseAgent, AgentResponse
from prompts.system_prompts import FLAG_REPORTER_AGENT_PROMPT
from config.gemini_config import GeminiClient

logger = logging.getLogger(__name__)


class FlagReporterAgent(BaseAgent):
    """
    Agent responsible for generating comprehensive learning reports.
    Analyzes mistakes, identifies gaps, and provides recommendations.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Flag Reporter Agent.

        Args:
            gemini_client: Gemini API client instance
        """
        super().__init__(
            gemini_client=gemini_client,
            agent_name="FlagReporterAgent",
            system_prompt=FLAG_REPORTER_AGENT_PROMPT,
            temperature=0.6
        )

    def process(
        self,
        user_id: str,
        pdf_id: str,
        session_data: Dict[str, Any]
    ) -> AgentResponse:
        """
        Generate personalized learning report.

        Args:
            user_id: User identifier
            pdf_id: PDF identifier
            session_data: User's learning session data

        Returns:
            AgentResponse: Comprehensive learning report
        """
        start_time = time.time()

        try:
            self.logger.info(f"Generating learning report for user {user_id}")

            # Analyze session data
            analysis = self.analyze_session_data(session_data)

            # Identify learning gaps
            gaps = self.identify_learning_gaps(session_data.get('mistakes', []))

            # Generate recommendations
            recommendations = self.generate_recommendations(gaps)

            # Create final report
            report = self.create_report(analysis, gaps, recommendations)

            result_data = {
                'user_id': user_id,
                'pdf_id': pdf_id,
                'report_data': report,
                'generated_at': datetime.utcnow().isoformat()
            }

            duration = time.time() - start_time
            self.log_performance('report_generation', duration, True)

            self.logger.info(
                f"Learning report generated",
                extra={
                    'user_id': user_id,
                    'accuracy': report.get('accuracy_percentage', 0),
                    'gaps': len(gaps),
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
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=self.agent_name,
                duration=time.time() - start_time
            )

    def analyze_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user's learning session data.

        Args:
            session_data: Session data with Q&A and mistakes

        Returns:
            dict: Analysis results
        """
        qa_sessions = session_data.get('qa_sessions', [])
        mistakes = session_data.get('mistakes', [])

        # Calculate statistics
        total_sessions = len(qa_sessions)
        total_mistakes = len(mistakes)

        # Count mistake types
        mistake_types = {}
        for mistake in mistakes:
            mtype = mistake.get('mistake_type', 'unknown')
            mistake_types[mtype] = mistake_types.get(mtype, 0) + 1

        # Calculate accuracy
        if total_sessions > 0:
            correct_responses = sum(
                1 for session in qa_sessions
                if session.get('confidence_score', 0) > 0.7
            )
            accuracy = (correct_responses / total_sessions) * 100
        else:
            accuracy = 100

        # Identify strengths
        strengths = []
        if mistake_types.get('grammar', 0) < total_mistakes * 0.3:
            strengths.append('Strong grammar foundation')
        if mistake_types.get('vocabulary', 0) < total_mistakes * 0.3:
            strengths.append('Good vocabulary usage')

        return {
            'total_sessions': total_sessions,
            'total_mistakes': total_mistakes,
            'mistake_types': mistake_types,
            'accuracy_percentage': round(accuracy, 2),
            'most_common_mistake_type': max(mistake_types.items(), key=lambda x: x[1])[0] if mistake_types else 'none',
            'strengths': strengths,
            'analysis_timestamp': time.time()
        }

    def identify_learning_gaps(self, mistakes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify learning gaps from mistakes.

        Args:
            mistakes: List of logged mistakes

        Returns:
            List[dict]: Identified learning gaps
        """
        if not mistakes:
            return []

        # Group mistakes by type and topic
        gap_analysis = {}

        for mistake in mistakes:
            mtype = mistake.get('mistake_type', 'unknown')
            context = mistake.get('context', 'General')

            key = f"{mtype}_{context}"
            if key not in gap_analysis:
                gap_analysis[key] = {
                    'type': mtype,
                    'topic': context,
                    'count': 0,
                    'examples': []
                }

            gap_analysis[key]['count'] += 1
            gap_analysis[key]['examples'].append(mistake.get('mistake_text', ''))

        # Convert to gaps with severity
        gaps = []
        for key, data in gap_analysis.items():
            severity = 'Low'
            if data['count'] >= 5:
                severity = 'High'
            elif data['count'] >= 3:
                severity = 'Medium'

            gaps.append({
                'topic': f"{data['type'].title()} - {data['topic']}",
                'description': f"Recurring {data['type']} issues in {data['topic']}",
                'severity': severity,
                'evidence': data['examples'][:3],  # Top 3 examples
                'recommendations': self._get_gap_recommendations(data['type'])
            })

        # Sort by severity
        severity_order = {'High': 3, 'Medium': 2, 'Low': 1}
        gaps.sort(key=lambda x: severity_order[x['severity']], reverse=True)

        return gaps

    def _get_gap_recommendations(self, mistake_type: str) -> List[str]:
        """Get recommendations for specific mistake type"""
        recommendations_map = {
            'grammar': [
                'Review grammar rules for this topic',
                'Practice grammar exercises daily',
                'Study example sentences'
            ],
            'vocabulary': [
                'Build vocabulary with flashcards',
                'Read more content in target language',
                'Practice using new words in sentences'
            ],
            'syntax': [
                'Study sentence structure patterns',
                'Practice reordering sentences',
                'Analyze native speaker examples'
            ],
            'pronunciation': [
                'Listen to native speakers',
                'Practice pronunciation daily',
                'Record yourself speaking'
            ],
            'fluency': [
                'Practice speaking regularly',
                'Engage in conversations',
                'Read aloud to improve flow'
            ]
        }

        return recommendations_map.get(mistake_type, ['Continue practicing'])

    def generate_recommendations(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations.

        Args:
            gaps: Identified learning gaps

        Returns:
            List[dict]: Prioritized recommendations
        """
        recommendations = []

        for gap in gaps[:5]:  # Top 5 gaps
            severity = gap['severity']
            topic = gap['topic']

            priority = 'High' if severity == 'High' else 'Medium' if severity == 'Medium' else 'Low'

            recommendations.append({
                'priority': priority,
                'action': f"Focus on: {topic}",
                'reason': f"This area needs {severity.lower()} priority attention",
                'estimated_time': '15-30 minutes daily' if priority == 'High' else '10-15 minutes daily'
            })

        # Add general recommendations
        recommendations.append({
            'priority': 'Medium',
            'action': 'Practice consistently every day',
            'reason': 'Consistency is key to language learning',
            'estimated_time': '20-30 minutes daily'
        })

        return recommendations

    def create_report(
        self,
        analysis: Dict[str, Any],
        gaps: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create final comprehensive report.

        Args:
            analysis: Session analysis
            gaps: Learning gaps
            recommendations: Recommendations

        Returns:
            dict: Complete report
        """
        # Generate summary
        accuracy = analysis['accuracy_percentage']
        if accuracy >= 85:
            summary_tone = "Excellent progress!"
        elif accuracy >= 70:
            summary_tone = "Good progress with room for improvement."
        else:
            summary_tone = "Keep practicing - improvement takes time."

        summary = f"{summary_tone} You've completed {analysis['total_sessions']} sessions with {accuracy:.1f}% accuracy."

        # Determine next steps
        next_steps = []
        if gaps:
            next_steps.append(f"Address {gaps[0]['topic']} first")
        next_steps.append("Practice for 20 minutes daily")
        next_steps.append("Review your mistakes regularly")

        # Generate motivation message
        motivation = self._generate_motivation_message(analysis)

        # Weekly goal
        if accuracy < 70:
            weekly_goal = "Increase accuracy to 75% by practicing fundamentals"
        elif accuracy < 85:
            weekly_goal = "Achieve 85% accuracy by focusing on weak areas"
        else:
            weekly_goal = "Maintain accuracy above 85% and expand vocabulary"

        return {
            'summary': summary,
            'learning_gaps': gaps,
            'accuracy_percentage': accuracy,
            'total_sessions': analysis['total_sessions'],
            'total_mistakes': analysis['total_mistakes'],
            'mistakes_by_type': analysis['mistake_types'],
            'most_common_mistake_type': analysis['most_common_mistake_type'],
            'strengths': analysis.get('strengths', []),
            'improvements_needed': [gap['topic'] for gap in gaps[:3]],
            'recommendations': recommendations,
            'next_steps': next_steps,
            'motivation_message': motivation,
            'weekly_goal': weekly_goal
        }

    def _generate_motivation_message(self, analysis: Dict[str, Any]) -> str:
        """Generate personalized motivation message"""
        accuracy = analysis['accuracy_percentage']
        sessions = analysis['total_sessions']

        if accuracy >= 85:
            return f"🌟 Outstanding! You've maintained {accuracy:.1f}% accuracy over {sessions} sessions. Keep up the amazing work!"
        elif accuracy >= 70:
            return f"👍 Great job! {accuracy:.1f}% accuracy shows real progress. Keep practicing and you'll master this!"
        else:
            return f"💪 You're learning! Every mistake is a step forward. Keep practicing and you'll see improvement!"

