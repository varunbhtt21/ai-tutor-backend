"""
Student Tracking Service - Real-time comprehensive student interaction tracking
Building on the existing analytics foundation with enhanced real-time capabilities
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlmodel import Session, select, and_, or_, func
from sqlalchemy import desc

from app.models.analytics import (
    StudentSessionTracking, ChatInteraction, CodeInteraction, CodeSubmission,
    StruggleAnalysis, StudentLearningProfile, EventLog, EventType,
    MessageType, StruggleSeverity
)
from app.models.session import Session as SessionModel
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class StudentTrackingService:
    """Comprehensive real-time student tracking and analytics service"""
    
    def __init__(self):
        """Initialize the tracking service"""
        self.struggle_threshold = 70.0  # Configurable threshold for struggle detection
        self.critical_threshold = 85.0  # Critical struggle threshold
        
        # WebSocket manager will be injected to avoid circular imports
        self.websocket_manager = None
        
    async def initialize_session_tracking(
        self,
        session_id: int,
        student_id: int,
        db: Session
    ) -> StudentSessionTracking:
        """Initialize or retrieve session tracking for a student"""
        
        # Check if tracking already exists for this session
        statement = select(StudentSessionTracking).where(
            and_(
                StudentSessionTracking.session_id == session_id,
                StudentSessionTracking.student_id == student_id
            )
        )
        existing_tracking = db.exec(statement).first()
        
        if existing_tracking:
            # Update last activity
            existing_tracking.last_activity = datetime.utcnow()
            db.add(existing_tracking)
            db.commit()
            db.refresh(existing_tracking)
            return existing_tracking
        
        # Create new session tracking
        session_tracking = StudentSessionTracking(
            session_id=session_id,
            student_id=student_id,
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        db.add(session_tracking)
        db.commit()
        db.refresh(session_tracking)
        
        logger.info(f"Initialized session tracking for student {student_id} in session {session_id}")
        return session_tracking
    
    async def track_chat_interaction(
        self,
        session_tracking_id: int,
        student_id: int,
        session_id: int,
        message_type: MessageType,
        content: str,
        node_id: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        db: Session = None
    ) -> ChatInteraction:
        """Track a detailed chat interaction"""
        
        # Analyze message content
        word_count = len(content.split())
        character_count = len(content)
        emotional_tone = self._analyze_emotional_tone(content)
        intent_classification = self._classify_intent(content, message_type)
        complexity_score = self._calculate_message_complexity(content)
        
        # Create chat interaction record
        chat_interaction = ChatInteraction(
            session_tracking_id=session_tracking_id,
            student_id=student_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            message_type=message_type,
            content=content,
            node_id=node_id,
            response_time_ms=response_time_ms,
            character_count=character_count,
            word_count=word_count,
            emotional_tone=emotional_tone,
            intent_classification=intent_classification,
            complexity_score=complexity_score
        )
        
        db.add(chat_interaction)
        
        # Update session tracking metrics
        await self._update_session_chat_metrics(session_tracking_id, db)
        
        # Check for struggle indicators in chat
        await self._analyze_chat_for_struggle_indicators(
            session_tracking_id, student_id, session_id, content, emotional_tone, db
        )
        
        db.commit()
        db.refresh(chat_interaction)
        
        logger.debug(f"Tracked chat interaction for student {student_id}: {intent_classification}")
        return chat_interaction
    
    async def track_code_interaction(
        self,
        session_tracking_id: int,
        student_id: int,
        session_id: int,
        code_snapshot: str,
        interaction_type: str = "keypress",
        node_id: Optional[str] = None,
        language: str = "python",
        previous_code: Optional[str] = None,
        db: Session = None
    ) -> Optional[CodeInteraction]:
        """Track code changes with intelligent batching"""
        
        # Calculate code metrics
        lines_of_code = len([line for line in code_snapshot.split('\n') if line.strip()])
        
        # Calculate differences if previous code available
        code_diff = None
        chars_added = 0
        chars_deleted = 0
        is_significant = False
        
        if previous_code:
            code_diff = self._calculate_code_diff(previous_code, code_snapshot)
            chars_added, chars_deleted = self._count_character_changes(previous_code, code_snapshot)
            is_significant = self._is_significant_change(previous_code, code_snapshot)
        else:
            chars_added = len(code_snapshot)
            is_significant = len(code_snapshot) > 10  # More than trivial typing
        
        # Only record significant changes to avoid excessive noise
        if is_significant or interaction_type in ["run", "submit", "paste"]:
            
            # Analyze code for errors (basic syntax check)
            syntax_errors = self._analyze_syntax_errors(code_snapshot, language)
            completion_progress = self._estimate_completion_progress(code_snapshot, node_id)
            
            code_interaction = CodeInteraction(
                session_tracking_id=session_tracking_id,
                student_id=student_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                node_id=node_id,
                interaction_type=interaction_type,
                code_snapshot=code_snapshot,
                code_diff=code_diff,
                language=language,
                characters_added=chars_added,
                characters_deleted=chars_deleted,
                lines_of_code=lines_of_code,
                syntax_errors=syntax_errors,
                is_significant_change=is_significant,
                completion_progress=completion_progress
            )
            
            db.add(code_interaction)
            
            # Update session tracking metrics
            await self._update_session_code_metrics(session_tracking_id, db)
            
            # Analyze for struggle indicators in code patterns
            await self._analyze_code_for_struggle_indicators(
                session_tracking_id, student_id, session_id, code_snapshot, 
                syntax_errors, interaction_type, db
            )
            
            db.commit()
            db.refresh(code_interaction)
            
            logger.debug(f"Tracked code interaction for student {student_id}: {interaction_type}")
            return code_interaction
        
        return None
    
    def set_websocket_manager(self, manager):
        """Set the WebSocket manager for real-time notifications"""
        self.websocket_manager = manager
    
    async def notify_struggle_alert(
        self,
        session_id: int,
        student_id: int,
        struggle_analysis: StruggleAnalysis,
        db: Session
    ):
        """Send real-time struggle alert to instructors"""
        if not self.websocket_manager:
            return
        
        # Get student details
        student = db.get(User, student_id)
        student_name = f"{student.first_name} {student.last_name}" if student else f"Student {student_id}"
        
        alert_data = {
            "student_id": student_id,
            "student_name": student_name,
            "struggle_id": struggle_analysis.id,
            "node_id": struggle_analysis.node_id,
            "struggle_score": struggle_analysis.struggle_score,
            "severity": struggle_analysis.severity.value,
            "indicators": struggle_analysis.indicators,
            "recommendations": struggle_analysis.recommendations,
            "intervention_suggested": struggle_analysis.intervention_suggested,
            "timestamp": struggle_analysis.timestamp.isoformat()
        }
        
        await self.websocket_manager.send_struggle_alert(session_id, alert_data)
    
    async def notify_progress_update(
        self,
        session_id: int,
        student_id: int,
        progress_data: Dict[str, Any]
    ):
        """Send real-time progress updates"""
        if not self.websocket_manager:
            return
        
        await self.websocket_manager.send_progress_update(
            session_id, student_id, progress_data
        )
    
    async def get_session_overview(self, session_id: int, db: Session = None) -> Dict[str, Any]:
        """Get comprehensive session overview for instructor dashboard"""
        if not db:
            return {"error": "Database session required"}
        
        # Get all active session trackings
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.session_id == session_id
        )
        session_trackings = db.exec(statement).all()
        
        students_data = []
        for tracking in session_trackings:
            student = db.get(User, tracking.student_id)
            student_name = f"{student.first_name} {student.last_name}" if student else f"Student {tracking.student_id}"
            
            # Get recent struggle analysis
            recent_struggle = db.exec(
                select(StruggleAnalysis)
                .where(StruggleAnalysis.session_tracking_id == tracking.id)
                .order_by(desc(StruggleAnalysis.timestamp))
            ).first()
            
            students_data.append({
                "student_id": tracking.student_id,
                "student_name": student_name,
                "progress_percentage": tracking.progress_percentage,
                "current_node_id": tracking.current_node_id,
                "active_time_minutes": tracking.active_time_seconds / 60,
                "total_interactions": tracking.total_interactions,
                "struggle_score": tracking.current_struggle_score,
                "is_struggling": tracking.current_struggle_score > self.struggle_threshold,
                "last_activity": tracking.last_activity.isoformat(),
                "recent_struggle": {
                    "severity": recent_struggle.severity.value if recent_struggle else "none",
                    "indicators": recent_struggle.indicators if recent_struggle else {}
                } if recent_struggle else None
            })
        
        return {
            "session_id": session_id,
            "total_students": len(students_data),
            "struggling_students": len([s for s in students_data if s["is_struggling"]]),
            "average_progress": sum(s["progress_percentage"] for s in students_data) / len(students_data) if students_data else 0,
            "students": students_data
        }
    
    async def get_detailed_student_analytics(
        self,
        student_id: int,
        session_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific student"""
        
        # Get session tracking
        tracking = db.exec(
            select(StudentSessionTracking).where(
                and_(
                    StudentSessionTracking.session_id == session_id,
                    StudentSessionTracking.student_id == student_id
                )
            )
        ).first()
        
        if not tracking:
            return {"error": "No tracking data found"}
        
        # Get recent interactions
        recent_chats = db.exec(
            select(ChatInteraction)
            .where(ChatInteraction.session_tracking_id == tracking.id)
            .order_by(desc(ChatInteraction.timestamp))
            .limit(10)
        ).all()
        
        recent_code = db.exec(
            select(CodeInteraction)
            .where(CodeInteraction.session_tracking_id == tracking.id)
            .order_by(desc(CodeInteraction.timestamp))
            .limit(10)
        ).all()
        
        recent_submissions = db.exec(
            select(CodeSubmission)
            .where(CodeSubmission.session_tracking_id == tracking.id)
            .order_by(desc(CodeSubmission.timestamp))
            .limit(5)
        ).all()
        
        return {
            "student_id": student_id,
            "session_tracking": {
                "progress_percentage": tracking.progress_percentage,
                "current_node_id": tracking.current_node_id,
                "total_interactions": tracking.total_interactions,
                "active_time_minutes": tracking.active_time_seconds / 60,
                "struggle_score": tracking.current_struggle_score,
                "nodes_completed": tracking.nodes_completed,
                "engagement_patterns": tracking.engagement_patterns
            },
            "recent_activity": {
                "chat_messages": [
                    {
                        "timestamp": chat.timestamp.isoformat(),
                        "message_type": chat.message_type.value,
                        "content": chat.content[:100] + "..." if len(chat.content) > 100 else chat.content,
                        "emotional_tone": chat.emotional_tone,
                        "node_id": chat.node_id
                    }
                    for chat in recent_chats
                ],
                "code_changes": [
                    {
                        "timestamp": code.timestamp.isoformat(),
                        "interaction_type": code.interaction_type,
                        "lines_of_code": code.lines_of_code,
                        "syntax_errors": len(code.syntax_errors),
                        "completion_progress": code.completion_progress,
                        "node_id": code.node_id
                    }
                    for code in recent_code
                ],
                "submissions": [
                    {
                        "timestamp": sub.timestamp.isoformat(),
                        "node_id": sub.node_id,
                        "is_correct": sub.is_correct,
                        "score": sub.score,
                        "execution_time_ms": sub.execution_time_ms
                    }
                    for sub in recent_submissions
                ]
            }
        }
    
    async def acknowledge_struggle_intervention(
        self,
        struggle_id: int,
        db: Session
    ):
        """Mark a struggle intervention as acknowledged by instructor"""
        struggle = db.get(StruggleAnalysis, struggle_id)
        if struggle:
            struggle.instructor_notified = True
            struggle.instructor_response_time_seconds = int(
                (datetime.utcnow() - struggle.timestamp).total_seconds()
            )
            db.add(struggle)
            db.commit()
            
            logger.info(f"Struggle intervention {struggle_id} acknowledged by instructor")
    
    async def track_code_submission(
        self,
        session_tracking_id: int,
        student_id: int,
        session_id: int,
        node_id: str,
        submitted_code: str,
        is_correct: bool,
        test_results: Dict[str, Any],
        language: str = "python",
        execution_time_ms: Optional[int] = None,
        ai_feedback: Optional[str] = None,
        db: Session = None
    ) -> CodeSubmission:
        """Track code submission and evaluation results"""
        
        # Count previous submissions for this node
        statement = select(func.count(CodeSubmission.id)).where(
            and_(
                CodeSubmission.session_tracking_id == session_tracking_id,
                CodeSubmission.node_id == node_id
            )
        )
        submission_count = db.exec(statement).first() or 0
        submission_number = submission_count + 1
        
        # Calculate time since session start
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        time_since_start = 0
        if session_tracking:
            time_since_start = int((datetime.utcnow() - session_tracking.start_time).total_seconds())
        
        # Get time since last attempt
        statement = select(CodeSubmission).where(
            and_(
                CodeSubmission.session_tracking_id == session_tracking_id,
                CodeSubmission.node_id == node_id
            )
        ).order_by(desc(CodeSubmission.timestamp)).limit(1)
        
        last_submission = db.exec(statement).first()
        time_since_last_attempt = None
        if last_submission:
            time_since_last_attempt = int((datetime.utcnow() - last_submission.timestamp).total_seconds())
        
        # Analyze errors
        compilation_errors, runtime_errors, logic_errors = self._categorize_errors(test_results)
        
        code_submission = CodeSubmission(
            session_tracking_id=session_tracking_id,
            student_id=student_id,
            session_id=session_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            submission_number=submission_number,
            submitted_code=submitted_code,
            language=language,
            is_correct=is_correct,
            test_results=test_results,
            execution_time_ms=execution_time_ms,
            compilation_errors=compilation_errors,
            runtime_errors=runtime_errors,
            logic_errors=logic_errors,
            ai_feedback=ai_feedback,
            time_since_start_seconds=time_since_start,
            time_since_last_attempt_seconds=time_since_last_attempt
        )
        
        db.add(code_submission)
        
        # Update session tracking with submission results
        await self._update_session_submission_metrics(session_tracking_id, is_correct, db)
        
        # Analyze for struggle patterns based on submission
        await self._analyze_submission_for_struggle(
            session_tracking_id, student_id, session_id, node_id,
            is_correct, submission_number, compilation_errors, runtime_errors, db
        )
        
        db.commit()
        db.refresh(code_submission)
        
        logger.info(f"Tracked code submission for student {student_id}, node {node_id}: {'SUCCESS' if is_correct else 'FAILED'}")
        return code_submission
    
    async def detect_real_time_struggle(
        self,
        session_tracking_id: int,
        student_id: int,
        session_id: int,
        node_id: Optional[str] = None,
        db: Session = None
    ) -> Optional[StruggleAnalysis]:
        """Detect and analyze student struggle in real-time"""
        
        # Get recent activity (last 10 minutes)
        recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
        
        # Analyze multiple struggle indicators
        indicators = {}
        
        # 1. Chat-based indicators
        chat_indicators = await self._analyze_chat_struggle_indicators(
            session_tracking_id, recent_cutoff, db
        )
        indicators.update(chat_indicators)
        
        # 2. Code-based indicators
        code_indicators = await self._analyze_code_struggle_indicators(
            session_tracking_id, recent_cutoff, db
        )
        indicators.update(code_indicators)
        
        # 3. Submission-based indicators
        submission_indicators = await self._analyze_submission_struggle_indicators(
            session_tracking_id, node_id, db
        )
        indicators.update(submission_indicators)
        
        # 4. Time-based indicators
        time_indicators = await self._analyze_time_struggle_indicators(
            session_tracking_id, recent_cutoff, db
        )
        indicators.update(time_indicators)
        
        # Calculate overall struggle score
        struggle_score = self._calculate_struggle_score(indicators)
        
        # Determine severity
        severity = self._determine_struggle_severity(struggle_score)
        
        # Only create record if there's significant struggle
        if struggle_score >= 30.0:  # Minimum threshold for recording
            
            # Generate AI analysis and recommendations
            ai_analysis = self._generate_struggle_analysis(indicators, struggle_score)
            recommendations = self._generate_struggle_recommendations(indicators)
            
            struggle_analysis = StruggleAnalysis(
                session_tracking_id=session_tracking_id,
                student_id=student_id,
                session_id=session_id,
                node_id=node_id,
                timestamp=datetime.utcnow(),
                struggle_score=struggle_score,
                severity=severity,
                indicators=indicators,
                ai_analysis=ai_analysis,
                recommendations=recommendations,
                intervention_suggested=struggle_score >= self.struggle_threshold
            )
            
            db.add(struggle_analysis)
            
            # Update session tracking struggle metrics
            await self._update_session_struggle_metrics(session_tracking_id, struggle_score, db)
            
            db.commit()
            db.refresh(struggle_analysis)
            
            logger.warning(f"Struggle detected for student {student_id}: {severity.value} (score: {struggle_score:.1f})")
            
            # Send real-time alert to instructors if intervention is suggested
            if struggle_analysis.intervention_suggested:
                await self.notify_struggle_alert(session_id, student_id, struggle_analysis, db)
            
            return struggle_analysis
        
        return None
    
    async def update_learning_profile(
        self,
        student_id: int,
        db: Session
    ) -> StudentLearningProfile:
        """Update or create student learning profile based on accumulated data"""
        
        # Get or create learning profile
        statement = select(StudentLearningProfile).where(
            StudentLearningProfile.student_id == student_id
        )
        profile = db.exec(statement).first()
        
        if not profile:
            profile = StudentLearningProfile(
                student_id=student_id,
                created_at=datetime.utcnow()
            )
            db.add(profile)
        
        # Analyze all session data for this student
        profile_data = await self._analyze_student_learning_patterns(student_id, db)
        
        # Update profile with new insights
        profile.last_updated = datetime.utcnow()
        profile.learning_style = profile_data.get("learning_style")
        profile.learning_style_confidence = profile_data.get("learning_style_confidence", 0.0)
        profile.preferred_time_of_day = profile_data.get("preferred_time_of_day")
        profile.average_session_duration_minutes = profile_data.get("avg_session_duration", 0.0)
        profile.average_response_time_ms = profile_data.get("avg_response_time", 0.0)
        profile.preferred_help_method = profile_data.get("preferred_help_method")
        profile.common_struggle_areas = profile_data.get("struggle_areas", [])
        profile.struggle_recovery_methods = profile_data.get("recovery_methods", [])
        profile.resilience_score = profile_data.get("resilience_score", 50.0)
        profile.motivation_drivers = profile_data.get("motivation_drivers", [])
        profile.overall_success_rate = profile_data.get("success_rate", 0.0)
        profile.consistency_score = profile_data.get("consistency_score", 50.0)
        profile.total_sessions = profile_data.get("total_sessions", 0)
        profile.total_study_time_hours = profile_data.get("total_study_hours", 0.0)
        profile.last_activity_date = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated learning profile for student {student_id}")
        return profile
    
    # Private helper methods for analysis
    
    def _analyze_emotional_tone(self, content: str) -> str:
        """Analyze emotional tone of message content"""
        content_lower = content.lower()
        
        # Frustration indicators
        frustration_words = ["stuck", "confused", "don't understand", "help", "frustrated", "hard", "difficult"]
        if any(word in content_lower for word in frustration_words):
            return "frustrated"
        
        # Positive indicators
        positive_words = ["thank", "got it", "understand", "clear", "yes", "perfect", "great"]
        if any(word in content_lower for word in positive_words):
            return "positive"
        
        # Question indicators
        if "?" in content or content_lower.startswith(("what", "how", "why", "when", "where", "can")):
            return "questioning"
        
        return "neutral"
    
    def _classify_intent(self, content: str, message_type: MessageType) -> str:
        """Classify the intent of a message"""
        content_lower = content.lower()
        
        if message_type == MessageType.HINT_REQUEST:
            return "hint_request"
        
        # Help request indicators
        help_indicators = ["help", "stuck", "don't know", "confused"]
        if any(indicator in content_lower for indicator in help_indicators):
            return "help_request"
        
        # Clarification indicators
        clarification_indicators = ["what does", "what is", "explain", "clarify", "mean"]
        if any(indicator in content_lower for indicator in clarification_indicators):
            return "clarification"
        
        # Code-related question
        code_indicators = ["code", "function", "variable", "error", "bug", "syntax"]
        if any(indicator in content_lower for indicator in code_indicators):
            return "code_question"
        
        return "general_question"
    
    def _calculate_message_complexity(self, content: str) -> float:
        """Calculate complexity score of a message (1-10 scale)"""
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Base complexity on length and structure
        complexity = min(10.0, (word_count / 10) + (sentence_count / 2))
        return max(1.0, complexity)
    
    def _calculate_code_diff(self, old_code: str, new_code: str) -> str:
        """Calculate a simple diff between code versions"""
        # Simple diff implementation - could be enhanced with proper diff algorithms
        if len(new_code) > len(old_code):
            return f"+{len(new_code) - len(old_code)} chars"
        elif len(new_code) < len(old_code):
            return f"-{len(old_code) - len(new_code)} chars"
        else:
            return "modified"
    
    def _count_character_changes(self, old_code: str, new_code: str) -> Tuple[int, int]:
        """Count characters added and deleted"""
        old_len = len(old_code)
        new_len = len(new_code)
        
        if new_len > old_len:
            return new_len - old_len, 0
        elif new_len < old_len:
            return 0, old_len - new_len
        else:
            # Same length but potentially different content
            differences = sum(1 for a, b in zip(old_code, new_code) if a != b)
            return differences // 2, differences // 2
    
    def _is_significant_change(self, old_code: str, new_code: str) -> bool:
        """Determine if code change is significant (not just typos)"""
        char_diff = abs(len(new_code) - len(old_code))
        
        # Significant if more than 5 character difference
        if char_diff > 5:
            return True
        
        # Or if it looks like actual code (contains keywords)
        code_keywords = ["def", "class", "if", "for", "while", "return", "import", "from"]
        if any(keyword in new_code.lower() for keyword in code_keywords):
            return True
        
        return False
    
    def _analyze_syntax_errors(self, code: str, language: str) -> List[str]:
        """Basic syntax error detection"""
        errors = []
        
        if language == "python":
            # Basic Python syntax checks
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    # Check for basic syntax issues
                    if line.count('(') != line.count(')'):
                        errors.append(f"Line {i+1}: Mismatched parentheses")
                    if line.count('[') != line.count(']'):
                        errors.append(f"Line {i+1}: Mismatched brackets")
                    if line.count('{') != line.count('}'):
                        errors.append(f"Line {i+1}: Mismatched braces")
        
        return errors
    
    def _estimate_completion_progress(self, code: str, node_id: Optional[str]) -> float:
        """Estimate how complete the code solution is (0-1 scale)"""
        if not code.strip():
            return 0.0
        
        # Basic heuristics for completion
        indicators = [
            "def " in code,  # Function definition
            "return" in code,  # Return statement
            len(code.split('\n')) > 3,  # Multiple lines
            "if" in code or "for" in code or "while" in code,  # Control structures
        ]
        
        return sum(indicators) / len(indicators)
    
    def _categorize_errors(self, test_results: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
        """Categorize errors from test results"""
        compilation_errors = test_results.get("compilation_errors", [])
        runtime_errors = test_results.get("runtime_errors", [])
        logic_errors = test_results.get("logic_errors", [])
        
        return compilation_errors, runtime_errors, logic_errors
    
    def _calculate_struggle_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall struggle score from various indicators"""
        score = 0.0
        
        # Weight different indicators
        weights = {
            "repetitive_questions": 15.0,
            "consecutive_errors": 20.0,
            "idle_time_minutes": 10.0,
            "help_requests": 12.0,
            "frustrated_messages": 18.0,
            "rapid_deletions": 8.0,
            "syntax_error_frequency": 10.0,
            "time_on_task_ratio": 7.0
        }
        
        for indicator, value in indicators.items():
            if indicator in weights and isinstance(value, (int, float)):
                normalized_value = min(1.0, value / 5.0)  # Normalize to 0-1
                score += weights[indicator] * normalized_value
        
        return min(100.0, score)
    
    def _determine_struggle_severity(self, struggle_score: float) -> StruggleSeverity:
        """Determine struggle severity based on score"""
        if struggle_score >= self.critical_threshold:
            return StruggleSeverity.CRITICAL
        elif struggle_score >= self.struggle_threshold:
            return StruggleSeverity.HIGH
        elif struggle_score >= 50.0:
            return StruggleSeverity.MEDIUM
        else:
            return StruggleSeverity.LOW
    
    def _generate_struggle_analysis(self, indicators: Dict[str, Any], score: float) -> str:
        """Generate AI analysis of struggle indicators"""
        # Simple rule-based analysis - could be enhanced with AI
        analysis_parts = []
        
        if indicators.get("repetitive_questions", 0) > 3:
            analysis_parts.append("Student is asking repetitive questions, indicating confusion about core concepts.")
        
        if indicators.get("consecutive_errors", 0) > 4:
            analysis_parts.append("Multiple consecutive errors suggest systematic misunderstanding.")
        
        if indicators.get("frustrated_messages", 0) > 0:
            analysis_parts.append("Student expressing frustration - may benefit from encouragement.")
        
        if indicators.get("idle_time_minutes", 0) > 5:
            analysis_parts.append("Extended idle time may indicate student is stuck or disengaged.")
        
        if not analysis_parts:
            analysis_parts.append("General struggle indicators detected - recommend checking in with student.")
        
        return " ".join(analysis_parts)
    
    def _generate_struggle_recommendations(self, indicators: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on struggle indicators"""
        recommendations = []
        
        if indicators.get("repetitive_questions", 0) > 2:
            recommendations.append("Provide clearer conceptual explanation")
            recommendations.append("Consider alternative teaching approach")
        
        if indicators.get("consecutive_errors", 0) > 3:
            recommendations.append("Break down problem into smaller steps")
            recommendations.append("Provide guided practice")
        
        if indicators.get("frustrated_messages", 0) > 0:
            recommendations.append("Offer encouragement and support")
            recommendations.append("Consider taking a short break")
        
        if indicators.get("syntax_error_frequency", 0) > 0.5:
            recommendations.append("Review syntax fundamentals")
            recommendations.append("Provide syntax reference guide")
        
        if not recommendations:
            recommendations.append("Monitor progress closely")
            recommendations.append("Consider offering assistance")
        
        return recommendations
    
    # Additional helper methods would be implemented here for:
    # - _update_session_chat_metrics()
    # - _update_session_code_metrics()
    # - _analyze_chat_for_struggle_indicators()
    # - _analyze_code_for_struggle_indicators()
    # - etc.
    
    async def _update_session_chat_metrics(self, session_tracking_id: int, db: Session):
        """Update session tracking with latest chat metrics"""
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        
        if session_tracking:
            session_tracking.total_chat_messages += 1
            session_tracking.last_activity = datetime.utcnow()
            db.add(session_tracking)
    
    async def _update_session_code_metrics(self, session_tracking_id: int, db: Session):
        """Update session tracking with latest code metrics"""
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        
        if session_tracking:
            session_tracking.total_code_changes += 1
            session_tracking.last_activity = datetime.utcnow()
            db.add(session_tracking)
    
    async def _update_session_submission_metrics(self, session_tracking_id: int, is_correct: bool, db: Session):
        """Update session tracking with submission results"""
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        
        if session_tracking:
            session_tracking.total_interactions += 1
            if not is_correct:
                session_tracking.consecutive_failures += 1
            else:
                session_tracking.consecutive_failures = 0
            
            # Recalculate success rate
            total_submissions = session_tracking.total_interactions
            if total_submissions > 0:
                # This is simplified - would need to query actual submission results
                pass
            
            session_tracking.last_activity = datetime.utcnow()
            db.add(session_tracking)
    
    async def _update_session_struggle_metrics(self, session_tracking_id: int, struggle_score: float, db: Session):
        """Update session tracking with struggle metrics"""
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        
        if session_tracking:
            session_tracking.current_struggle_score = struggle_score
            if struggle_score >= self.struggle_threshold:
                session_tracking.struggle_alerts_triggered += 1
            db.add(session_tracking)
    
    async def _analyze_chat_struggle_indicators(
        self, session_tracking_id: int, recent_cutoff: datetime, db: Session
    ) -> Dict[str, Any]:
        """Analyze chat interactions for struggle indicators"""
        
        statement = select(ChatInteraction).where(
            and_(
                ChatInteraction.session_tracking_id == session_tracking_id,
                ChatInteraction.timestamp >= recent_cutoff
            )
        )
        recent_chats = db.exec(statement).all()
        
        indicators = {}
        
        # Count frustrated messages
        frustrated_count = sum(1 for chat in recent_chats if chat.emotional_tone == "frustrated")
        indicators["frustrated_messages"] = frustrated_count
        
        # Count help requests
        help_requests = sum(1 for chat in recent_chats if chat.intent_classification == "help_request")
        indicators["help_requests"] = help_requests
        
        # Count repetitive questions (simplified)
        question_contents = [chat.content.lower() for chat in recent_chats if "?" in chat.content]
        similar_questions = 0
        for i, q1 in enumerate(question_contents):
            for q2 in question_contents[i+1:]:
                if len(set(q1.split()) & set(q2.split())) > 2:  # Share 3+ words
                    similar_questions += 1
        indicators["repetitive_questions"] = similar_questions
        
        return indicators
    
    async def _analyze_code_struggle_indicators(
        self, session_tracking_id: int, recent_cutoff: datetime, db: Session
    ) -> Dict[str, Any]:
        """Analyze code interactions for struggle indicators"""
        
        statement = select(CodeInteraction).where(
            and_(
                CodeInteraction.session_tracking_id == session_tracking_id,
                CodeInteraction.timestamp >= recent_cutoff
            )
        )
        recent_code = db.exec(statement).all()
        
        indicators = {}
        
        # Count rapid deletions (large character deletions)
        rapid_deletions = sum(1 for code in recent_code if code.characters_deleted > 50)
        indicators["rapid_deletions"] = rapid_deletions
        
        # Syntax error frequency
        total_interactions = len(recent_code)
        syntax_errors = sum(1 for code in recent_code if code.syntax_errors)
        indicators["syntax_error_frequency"] = syntax_errors / max(1, total_interactions)
        
        return indicators
    
    async def _analyze_submission_struggle_indicators(
        self, session_tracking_id: int, node_id: Optional[str], db: Session
    ) -> Dict[str, Any]:
        """Analyze submission patterns for struggle indicators"""
        
        statement = select(CodeSubmission).where(
            CodeSubmission.session_tracking_id == session_tracking_id
        )
        if node_id:
            statement = statement.where(CodeSubmission.node_id == node_id)
        
        submissions = db.exec(statement).all()
        
        indicators = {}
        
        # Count consecutive errors
        consecutive_errors = 0
        for submission in reversed(submissions):  # Most recent first
            if not submission.is_correct:
                consecutive_errors += 1
            else:
                break
        
        indicators["consecutive_errors"] = consecutive_errors
        
        return indicators
    
    async def _analyze_time_struggle_indicators(
        self, session_tracking_id: int, recent_cutoff: datetime, db: Session
    ) -> Dict[str, Any]:
        """Analyze time-based struggle indicators"""
        
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.id == session_tracking_id
        )
        session_tracking = db.exec(statement).first()
        
        indicators = {}
        
        if session_tracking:
            # Calculate idle time
            time_since_last_activity = (datetime.utcnow() - session_tracking.last_activity).total_seconds() / 60
            indicators["idle_time_minutes"] = time_since_last_activity
            
            # Time on task ratio (simplified)
            total_time = (datetime.utcnow() - session_tracking.start_time).total_seconds() / 60
            active_ratio = session_tracking.active_time_seconds / max(1, total_time * 60)
            indicators["time_on_task_ratio"] = 1.0 - active_ratio  # Inverted - higher is worse
        
        return indicators
    
    async def _analyze_student_learning_patterns(self, student_id: int, db: Session) -> Dict[str, Any]:
        """Analyze comprehensive learning patterns for a student"""
        
        # Get all session tracking data for student
        statement = select(StudentSessionTracking).where(
            StudentSessionTracking.student_id == student_id
        )
        all_sessions = db.exec(statement).all()
        
        if not all_sessions:
            return {}
        
        # Calculate various metrics
        total_sessions = len(all_sessions)
        total_time = sum(
            (session.end_time or datetime.utcnow() - session.start_time).total_seconds() / 3600
            for session in all_sessions
        )
        avg_session_duration = total_time / total_sessions if total_sessions > 0 else 0
        
        # Calculate overall success rate
        total_interactions = sum(session.total_interactions for session in all_sessions)
        # This would need more complex calculation based on actual submission data
        
        # Analyze time patterns (simplified)
        session_hours = [session.start_time.hour for session in all_sessions]
        if session_hours:
            avg_hour = sum(session_hours) / len(session_hours)
            if avg_hour < 12:
                preferred_time = "morning"
            elif avg_hour < 18:
                preferred_time = "afternoon"
            else:
                preferred_time = "evening"
        else:
            preferred_time = None
        
        return {
            "total_sessions": total_sessions,
            "total_study_hours": total_time,
            "avg_session_duration": avg_session_duration * 60,  # Convert to minutes
            "preferred_time_of_day": preferred_time,
            "success_rate": 0.75,  # Placeholder - would calculate from actual data
            "consistency_score": 85.0,  # Placeholder
            "learning_style": "visual",  # Would be determined by AI analysis
            "learning_style_confidence": 0.7,
            "avg_response_time": 2500.0,  # milliseconds
            "preferred_help_method": "hints",
            "struggle_areas": ["loops", "functions"],  # From struggle analysis
            "recovery_methods": ["hints", "examples"],
            "resilience_score": 75.0,
            "motivation_drivers": ["achievement", "progress"],
        } 