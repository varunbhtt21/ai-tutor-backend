"""
Bubble Evaluation Service - Validates student responses per bubble type
Enhanced evaluation with AI-powered assessment and adaptive feedback
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlmodel import Session

from app.models.session import BubbleNode, StudentState, BubbleType
from app.models.analytics import EventLog, EventType, MessageType
from app.schemas.ai_tutor import TutorRequest, TutorResponse
from app.services.ai_tutor_service import AITutorService
from app.services.student_tracking_service import StudentTrackingService

logger = logging.getLogger(__name__)


class BubbleEvaluationService:
    """Service for evaluating student responses across different bubble types"""
    
    def __init__(self):
        self.ai_tutor_service = AITutorService()
        self.tracking_service = StudentTrackingService()
    
    async def evaluate_concept_bubble(
        self,
        bubble_node: BubbleNode,
        student_response: Dict[str, Any],
        student_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Evaluate concept bubble completion
        
        Args:
            bubble_node: The concept bubble being evaluated
            student_response: Student's engagement data (time spent, questions asked, etc.)
            student_context: Student profile and session context
            db: Database session
            
        Returns:
            Evaluation result with completion status and feedback
        """
        try:
            # Extract engagement metrics
            time_spent = student_response.get('timeSpent', 0)
            questions_asked = student_response.get('questionsAsked', 0)
            confidence_level = student_response.get('confidence', 'low')
            readiness_score = student_response.get('readiness_score', 0)
            examples_requested = student_response.get('examples_requested', 0)
            
            # Minimum requirements for concept completion
            min_time_threshold = 60  # 1 minute minimum
            min_readiness_score = 70  # 70% readiness score
            
            # Evaluate completion criteria
            completion_criteria = {
                'sufficient_time': time_spent >= min_time_threshold,
                'adequate_readiness': readiness_score >= min_readiness_score,
                'engaged_learning': questions_asked > 0 or confidence_level in ['medium', 'high'],
                'content_understood': confidence_level != 'low'
            }
            
            # Calculate overall completion score
            criteria_met = sum(completion_criteria.values())
            total_criteria = len(completion_criteria)
            completion_percentage = (criteria_met / total_criteria) * 100
            
            # Determine if concept is mastered
            is_completed = completion_percentage >= 75  # 3 out of 4 criteria
            
            # Generate personalized feedback
            feedback = await self._generate_concept_feedback(
                bubble_node, student_response, completion_criteria, db
            )
            
            # Calculate coin reward based on performance
            base_reward = bubble_node.coin_reward or 10
            performance_multiplier = min(readiness_score / 100, 1.0)
            coin_reward = int(base_reward * performance_multiplier) if is_completed else 0
            
            # Track the evaluation
            await self._track_concept_evaluation(
                bubble_node, student_context, completion_criteria, db
            )
            
            return {
                'success': is_completed,
                'completion_percentage': completion_percentage,
                'criteria_met': completion_criteria,
                'feedback': feedback,
                'coin_reward': coin_reward,
                'readiness_score': readiness_score,
                'time_spent': time_spent,
                'next_recommendations': await self._get_concept_recommendations(
                    bubble_node, is_completed, student_context, db
                )
            }
            
        except Exception as e:
            logger.error(f"Error evaluating concept bubble {bubble_node.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'feedback': 'An error occurred during evaluation. Please try again.'
            }
    
    async def evaluate_task_bubble(
        self,
        bubble_node: BubbleNode,
        student_response: Dict[str, Any],
        student_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Evaluate coding task bubble completion
        
        Args:
            bubble_node: The task bubble being evaluated
            student_response: Student's code submission and metrics
            student_context: Student profile and session context
            db: Database session
            
        Returns:
            Evaluation result with code analysis and feedback
        """
        try:
            # Extract submission data
            submitted_code = student_response.get('code', '')
            attempts = student_response.get('attempts', 1)
            time_spent = student_response.get('timeSpent', 0)
            hints_used = student_response.get('hintsUsed', 0)
            tests_passed = student_response.get('testsPassed', 0)
            total_tests = student_response.get('totalTests', 1)
            
            # Code quality analysis
            code_quality = await self._analyze_code_quality(submitted_code, bubble_node)
            
            # Test execution results
            test_success_rate = tests_passed / total_tests if total_tests > 0 else 0
            
            # Evaluate completion criteria
            completion_criteria = {
                'code_submitted': len(submitted_code.strip()) > 0,
                'tests_passing': test_success_rate >= 0.8,  # 80% of tests must pass
                'reasonable_attempts': attempts <= 5,  # Not too many failed attempts
                'good_code_quality': code_quality['score'] >= 60  # Basic quality threshold
            }
            
            # Calculate completion score
            criteria_met = sum(completion_criteria.values())
            total_criteria = len(completion_criteria)
            completion_percentage = (criteria_met / total_criteria) * 100
            
            # Task is completed if major criteria are met
            is_completed = (completion_criteria['code_submitted'] and 
                          completion_criteria['tests_passing'])
            
            # Generate AI-powered code feedback
            feedback = await self._generate_task_feedback(
                bubble_node, submitted_code, completion_criteria, code_quality, db
            )
            
            # Calculate coin reward
            base_reward = bubble_node.coin_reward or 15
            quality_bonus = code_quality['score'] / 100
            efficiency_bonus = max(0, 1 - (attempts - 1) * 0.1)  # Bonus for fewer attempts
            hint_penalty = hints_used * 0.1  # Small penalty for using hints
            
            final_multiplier = min(quality_bonus + efficiency_bonus - hint_penalty, 1.5)
            coin_reward = int(base_reward * final_multiplier) if is_completed else 0
            
            # Track the evaluation
            await self._track_task_evaluation(
                bubble_node, student_context, completion_criteria, code_quality, db
            )
            
            return {
                'success': is_completed,
                'completion_percentage': completion_percentage,
                'criteria_met': completion_criteria,
                'feedback': feedback,
                'coin_reward': coin_reward,
                'code_quality': code_quality,
                'test_results': {
                    'passed': tests_passed,
                    'total': total_tests,
                    'success_rate': test_success_rate
                },
                'performance_metrics': {
                    'attempts': attempts,
                    'time_spent': time_spent,
                    'hints_used': hints_used
                },
                'next_recommendations': await self._get_task_recommendations(
                    bubble_node, is_completed, code_quality, student_context, db
                )
            }
            
        except Exception as e:
            logger.error(f"Error evaluating task bubble {bubble_node.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'feedback': 'An error occurred during code evaluation. Please try again.'
            }
    
    async def evaluate_quiz_bubble(
        self,
        bubble_node: BubbleNode,
        student_response: Dict[str, Any],
        student_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Evaluate quiz bubble completion
        
        Args:
            bubble_node: The quiz bubble being evaluated
            student_response: Student's quiz answers and metrics
            student_context: Student profile and session context
            db: Database session
            
        Returns:
            Evaluation result with quiz analysis and feedback
        """
        try:
            # Extract quiz data
            answers = student_response.get('answers', {})
            score = student_response.get('score', 0)
            total_questions = student_response.get('totalQuestions', 1)
            correct_answers = student_response.get('correctAnswers', 0)
            time_spent = student_response.get('timeSpent', 0)
            attempts = student_response.get('attempts', 1)
            
            # Quiz evaluation criteria
            passing_score = 70  # 70% passing threshold
            min_time_per_question = 15  # 15 seconds minimum per question
            min_total_time = min_time_per_question * total_questions
            
            completion_criteria = {
                'passing_score': score >= passing_score,
                'all_questions_answered': len(answers) == total_questions,
                'sufficient_time': time_spent >= min_total_time,
                'reasonable_attempts': attempts <= 3
            }
            
            # Calculate completion percentage
            criteria_met = sum(completion_criteria.values())
            total_criteria = len(completion_criteria)
            completion_percentage = (criteria_met / total_criteria) * 100
            
            # Quiz is completed if passing score is achieved
            is_completed = completion_criteria['passing_score']
            
            # Analyze answer patterns for feedback
            answer_analysis = await self._analyze_quiz_answers(
                bubble_node, answers, correct_answers, total_questions, db
            )
            
            # Generate adaptive feedback
            feedback = await self._generate_quiz_feedback(
                bubble_node, student_response, completion_criteria, answer_analysis, db
            )
            
            # Calculate coin reward
            base_reward = bubble_node.coin_reward or 20
            score_multiplier = score / 100
            speed_bonus = max(0, 1 - (time_spent - min_total_time) / (min_total_time * 2))
            attempt_bonus = max(0, 1 - (attempts - 1) * 0.2)
            
            final_multiplier = min(score_multiplier + speed_bonus * 0.2 + attempt_bonus * 0.1, 1.3)
            coin_reward = int(base_reward * final_multiplier) if is_completed else 0
            
            # Track the evaluation
            await self._track_quiz_evaluation(
                bubble_node, student_context, completion_criteria, answer_analysis, db
            )
            
            return {
                'success': is_completed,
                'completion_percentage': completion_percentage,
                'criteria_met': completion_criteria,
                'feedback': feedback,
                'coin_reward': coin_reward,
                'quiz_results': {
                    'score': score,
                    'correct_answers': correct_answers,
                    'total_questions': total_questions,
                    'passing_threshold': passing_score
                },
                'answer_analysis': answer_analysis,
                'performance_metrics': {
                    'time_spent': time_spent,
                    'attempts': attempts,
                    'time_per_question': time_spent / total_questions if total_questions > 0 else 0
                },
                'next_recommendations': await self._get_quiz_recommendations(
                    bubble_node, is_completed, score, answer_analysis, student_context, db
                )
            }
            
        except Exception as e:
            logger.error(f"Error evaluating quiz bubble {bubble_node.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'feedback': 'An error occurred during quiz evaluation. Please try again.'
            }
    
    async def _analyze_code_quality(self, code: str, bubble_node: BubbleNode) -> Dict[str, Any]:
        """Analyze code quality and provide metrics"""
        try:
            # Basic code quality metrics
            lines = code.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            metrics = {
                'total_lines': len(lines),
                'code_lines': len(non_empty_lines),
                'has_comments': any('//' in line or '/*' in line or '#' in line for line in lines),
                'has_functions': any('function' in line or 'def ' in line for line in lines),
                'proper_indentation': self._check_indentation(lines),
                'meaningful_names': self._check_variable_names(code),
                'complexity_score': min(len(non_empty_lines) / 10, 1.0)  # Simplistic complexity
            }
            
            # Calculate overall quality score
            quality_factors = {
                'structure': 1 if metrics['has_functions'] else 0.5,
                'readability': 1 if metrics['has_comments'] else 0.7,
                'formatting': 1 if metrics['proper_indentation'] else 0.6,
                'naming': metrics['meaningful_names'],
                'length': min(metrics['code_lines'] / 5, 1.0)  # Prefer some substance
            }
            
            quality_score = (sum(quality_factors.values()) / len(quality_factors)) * 100
            
            return {
                'score': quality_score,
                'metrics': metrics,
                'suggestions': self._generate_code_suggestions(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            return {
                'score': 50,  # Default average score on error
                'metrics': {},
                'suggestions': ['Review your code structure and add comments for clarity.']
            }
    
    def _check_indentation(self, lines: List[str]) -> bool:
        """Check if code has consistent indentation"""
        indented_lines = [line for line in lines if line.startswith('  ') or line.startswith('\t')]
        return len(indented_lines) > 0 or len(lines) <= 3  # Allow simple scripts
    
    def _check_variable_names(self, code: str) -> float:
        """Check for meaningful variable names"""
        import re
        
        # Find variable declarations (simplified)
        var_patterns = [
            r'let\s+(\w+)',
            r'const\s+(\w+)',
            r'var\s+(\w+)',
            r'(\w+)\s*=',
        ]
        
        variables = []
        for pattern in var_patterns:
            variables.extend(re.findall(pattern, code))
        
        if not variables:
            return 0.8  # No variables found, neutral score
        
        # Check for meaningful names (length > 1, not just 'x', 'y', etc.)
        meaningful = sum(1 for var in variables if len(var) > 1 and var not in ['x', 'y', 'i', 'j', 'k'])
        return meaningful / len(variables) if variables else 0.8
    
    def _generate_code_suggestions(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate code improvement suggestions"""
        suggestions = []
        
        if not metrics.get('has_comments'):
            suggestions.append("Add comments to explain your code logic.")
        
        if not metrics.get('proper_indentation'):
            suggestions.append("Use consistent indentation to improve code readability.")
        
        if not metrics.get('has_functions'):
            suggestions.append("Consider breaking your code into functions for better organization.")
        
        if metrics.get('meaningful_names', 1.0) < 0.7:
            suggestions.append("Use more descriptive variable names.")
        
        if metrics.get('code_lines', 0) < 3:
            suggestions.append("Your solution seems quite brief. Consider if you've addressed all requirements.")
        
        return suggestions or ["Great job! Your code looks well-structured."]
    
    async def _generate_concept_feedback(
        self,
        bubble_node: BubbleNode,
        student_response: Dict[str, Any],
        completion_criteria: Dict[str, bool],
        db: Session
    ) -> str:
        """Generate personalized feedback for concept completion"""
        
        readiness_score = student_response.get('readiness_score', 0)
        confidence = student_response.get('confidence', 'low')
        questions_asked = student_response.get('questionsAsked', 0)
        
        if completion_criteria['adequate_readiness'] and completion_criteria['content_understood']:
            return f"Excellent work! You've demonstrated strong understanding of {bubble_node.title} with a {readiness_score}% readiness score. Your {confidence} confidence level and {questions_asked} questions show good engagement. Ready to move forward!"
        
        elif completion_criteria['sufficient_time'] and completion_criteria['engaged_learning']:
            return f"Good effort on {bubble_node.title}! You spent adequate time and showed engagement. Consider reviewing the key concepts to boost your confidence before proceeding."
        
        else:
            return f"You're making progress with {bubble_node.title}. Try asking more questions, spending additional time with the material, or requesting examples to improve your understanding."
    
    async def _generate_task_feedback(
        self,
        bubble_node: BubbleNode,
        code: str,
        completion_criteria: Dict[str, bool],
        code_quality: Dict[str, Any],
        db: Session
    ) -> str:
        """Generate personalized feedback for task completion"""
        
        if completion_criteria['tests_passing'] and completion_criteria['good_code_quality']:
            return f"Outstanding work on {bubble_node.title}! Your code passes all tests and demonstrates good quality (Score: {code_quality['score']:.0f}/100). " + " ".join(code_quality['suggestions'][:2])
        
        elif completion_criteria['tests_passing']:
            return f"Great job getting the tests to pass for {bubble_node.title}! Your solution works correctly. " + " ".join(code_quality['suggestions'][:2])
        
        elif completion_criteria['code_submitted']:
            return f"You've submitted code for {bubble_node.title}, but some tests aren't passing yet. Review the requirements and test your logic. " + " ".join(code_quality['suggestions'][:2])
        
        else:
            return f"Please submit your code solution for {bubble_node.title}. Take your time to understand the requirements and test your approach."
    
    async def _generate_quiz_feedback(
        self,
        bubble_node: BubbleNode,
        student_response: Dict[str, Any],
        completion_criteria: Dict[str, bool],
        answer_analysis: Dict[str, Any],
        db: Session
    ) -> str:
        """Generate personalized feedback for quiz completion"""
        
        score = student_response.get('score', 0)
        attempts = student_response.get('attempts', 1)
        
        if completion_criteria['passing_score']:
            if score >= 90:
                return f"Exceptional performance on {bubble_node.title}! You scored {score}% on attempt {attempts}. Your understanding of the concepts is excellent."
            elif score >= 80:
                return f"Great work on {bubble_node.title}! You scored {score}% and demonstrated solid understanding. Keep up the excellent effort!"
            else:
                return f"Good job passing {bubble_node.title} with {score}%! You've met the requirements and can proceed with confidence."
        
        else:
            weak_areas = answer_analysis.get('weak_areas', [])
            if weak_areas:
                return f"You scored {score}% on {bubble_node.title}. Focus on reviewing: {', '.join(weak_areas[:3])}. Consider retaking after studying these areas."
            else:
                return f"You scored {score}% on {bubble_node.title}. Review the material and try again. You're close to passing!"
    
    async def _analyze_quiz_answers(
        self,
        bubble_node: BubbleNode,
        answers: Dict[str, Any],
        correct_answers: int,
        total_questions: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze quiz answer patterns"""
        
        # This would be more sophisticated with actual question data
        incorrect_count = total_questions - correct_answers
        accuracy_rate = correct_answers / total_questions if total_questions > 0 else 0
        
        # Simulate topic analysis based on performance
        weak_areas = []
        if accuracy_rate < 0.7:
            weak_areas = ["Core concepts", "Practical applications"]
        elif accuracy_rate < 0.8:
            weak_areas = ["Advanced topics"]
        
        return {
            'accuracy_rate': accuracy_rate,
            'correct_count': correct_answers,
            'incorrect_count': incorrect_count,
            'weak_areas': weak_areas,
            'performance_level': 'excellent' if accuracy_rate >= 0.9 else 'good' if accuracy_rate >= 0.7 else 'needs_improvement'
        }
    
    async def _get_concept_recommendations(
        self,
        bubble_node: BubbleNode,
        is_completed: bool,
        student_context: Dict[str, Any],
        db: Session
    ) -> List[str]:
        """Get next step recommendations for concept bubbles"""
        
        if is_completed:
            return [
                "Move on to the related practice tasks",
                "Take the quiz to test your knowledge",
                "Explore advanced topics in this area"
            ]
        else:
            return [
                "Review the key concepts again",
                "Ask more questions to clarify understanding",
                "Request additional examples",
                "Spend more time with the material"
            ]
    
    async def _get_task_recommendations(
        self,
        bubble_node: BubbleNode,
        is_completed: bool,
        code_quality: Dict[str, Any],
        student_context: Dict[str, Any],
        db: Session
    ) -> List[str]:
        """Get next step recommendations for task bubbles"""
        
        if is_completed:
            if code_quality['score'] >= 80:
                return [
                    "Excellent! Try a more challenging task",
                    "Review your solution and consider optimizations",
                    "Help others with similar problems"
                ]
            else:
                return [
                    "Good work! Try to improve code quality",
                    "Add comments and better variable names",
                    "Practice similar problems for fluency"
                ]
        else:
            return [
                "Debug your current solution step by step",
                "Break the problem into smaller parts",
                "Ask for hints if you're stuck",
                "Review related concept materials"
            ]
    
    async def _get_quiz_recommendations(
        self,
        bubble_node: BubbleNode,
        is_completed: bool,
        score: int,
        answer_analysis: Dict[str, Any],
        student_context: Dict[str, Any],
        db: Session
    ) -> List[str]:
        """Get next step recommendations for quiz bubbles"""
        
        if is_completed:
            return [
                "Great job! Move on to the next topic",
                "Try advanced quizzes in this area",
                "Apply your knowledge in practice tasks"
            ]
        else:
            weak_areas = answer_analysis.get('weak_areas', [])
            recommendations = ["Review the material and retake the quiz"]
            
            if weak_areas:
                recommendations.extend([f"Focus on studying: {area}" for area in weak_areas[:2]])
            
            recommendations.extend([
                "Ask questions about confusing topics",
                "Practice with similar examples"
            ])
            
            return recommendations
    
    async def _track_concept_evaluation(
        self,
        bubble_node: BubbleNode,
        student_context: Dict[str, Any],
        completion_criteria: Dict[str, bool],
        db: Session
    ):
        """Track concept evaluation for analytics"""
        # Implementation would log to analytics tables
        pass
    
    async def _track_task_evaluation(
        self,
        bubble_node: BubbleNode,
        student_context: Dict[str, Any],
        completion_criteria: Dict[str, bool],
        code_quality: Dict[str, Any],
        db: Session
    ):
        """Track task evaluation for analytics"""
        # Implementation would log to analytics tables
        pass
    
    async def _track_quiz_evaluation(
        self,
        bubble_node: BubbleNode,
        student_context: Dict[str, Any],
        completion_criteria: Dict[str, bool],
        answer_analysis: Dict[str, Any],
        db: Session
    ):
        """Track quiz evaluation for analytics"""
        # Implementation would log to analytics tables
        pass 