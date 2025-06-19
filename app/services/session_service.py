"""
Session service for managing student progress through bubble graphs
"""

from typing import List, Dict, Optional, Tuple, Any
import json
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.session import Session as SessionModel, StudentState, BubbleNode
from app.models.analytics import EventLog, CoinTransaction
from app.schemas.session import (
    BubbleGraphSchema, BubbleAdvanceRequest, BubbleAdvanceResponse,
    StudentStateResponse
)
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class SessionService:
    """Service for session and student progress management"""
    
    def __init__(self):
        self.graph_service = GraphService()
    
    def start_session(self, student_id: int, session_id: int, db: Session) -> StudentState:
        """Start a new session for a student"""
        try:
            # Get session
            session = db.get(SessionModel, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Check if student already has state for this session
            stmt = select(StudentState).where(
                StudentState.student_id == student_id,
                StudentState.session_id == session_id
            )
            existing_state = db.exec(stmt).first()
            
            if existing_state and not existing_state.is_completed:
                # Resume existing session
                existing_state.last_activity_at = datetime.utcnow()
                db.add(existing_state)
                db.commit()
                db.refresh(existing_state)
                return existing_state
            
            # Parse graph to get start node
            graph_data = BubbleGraphSchema(**session.graph_json)
            start_node = graph_data.start_node
            
            # Create new student state
            student_state = StudentState(
                student_id=student_id,
                session_id=session_id,
                current_node_id=start_node,
                completed_nodes=[],
                failed_attempts={},
                total_coins=0,
                is_completed=False,
                completion_percentage=0.0,
                started_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow(),
                total_time_spent=0
            )
            
            db.add(student_state)
            db.commit()
            db.refresh(student_state)
            
            # Log session start
            self._log_event(
                db, student_id, session_id, "session_started",
                {"start_node": start_node}
            )
            
            return student_state
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            db.rollback()
            raise
    
    def advance_bubble(
        self, 
        student_id: int, 
        session_id: int, 
        request: BubbleAdvanceRequest,
        db: Session
    ) -> BubbleAdvanceResponse:
        """Advance student to next bubble based on response"""
        try:
            # Get student state
            stmt = select(StudentState).where(
                StudentState.student_id == student_id,
                StudentState.session_id == session_id
            )
            student_state = db.exec(stmt).first()
            
            if not student_state:
                raise ValueError("Student state not found")
            
            if student_state.is_completed:
                return BubbleAdvanceResponse(
                    success=False,
                    feedback="Session already completed",
                    is_session_complete=True
                )
            
            # Get session and bubble data
            session = db.get(SessionModel, session_id)
            if not session:
                raise ValueError("Session not found")
            
            # Get bubble node details
            bubble_stmt = select(BubbleNode).where(
                BubbleNode.session_id == session_id,
                BubbleNode.node_id == request.node_id
            )
            bubble_node = db.exec(bubble_stmt).first()
            
            if not bubble_node:
                raise ValueError(f"Bubble node {request.node_id} not found")
            
            # Validate student response
            success, feedback, coins_earned = self._evaluate_response(
                bubble_node, request.student_response, request.code_output
            )
            
            # Update student state
            now = datetime.utcnow()
            time_spent = request.time_spent or 0
            student_state.last_activity_at = now
            student_state.total_time_spent += time_spent
            
            if success:
                # Mark bubble as completed
                if request.node_id not in student_state.completed_nodes:
                    student_state.completed_nodes.append(request.node_id)
                    student_state.total_coins += coins_earned
                    
                    # Award coins
                    if coins_earned > 0:
                        self._award_coins(db, student_id, session_id, coins_earned, 
                                        f"Completed bubble: {bubble_node.title}")
                
                # Get next node
                graph_data = BubbleGraphSchema(**session.graph_json)
                next_nodes = self.graph_service.get_next_nodes(graph_data, request.node_id)
                
                next_node_id = next_nodes[0] if next_nodes else None
                if next_node_id:
                    student_state.current_node_id = next_node_id
                else:
                    # Session completed
                    student_state.is_completed = True
                    student_state.completed_at = now
                    self._log_event(db, student_id, session_id, "session_completed", {
                        "total_time": student_state.total_time_spent,
                        "total_coins": student_state.total_coins
                    })
                
                # Update completion percentage
                total_nodes = len(graph_data.nodes)
                completed_count = len(student_state.completed_nodes)
                student_state.completion_percentage = (completed_count / total_nodes) * 100
                
                db.add(student_state)
                db.commit()
                
                # Log success
                self._log_event(db, student_id, session_id, "bubble_completed", {
                    "node_id": request.node_id,
                    "coins_earned": coins_earned,
                    "time_spent": time_spent
                })
                
                return BubbleAdvanceResponse(
                    success=True,
                    next_node_id=next_node_id,
                    feedback=feedback,
                    coins_earned=coins_earned,
                    is_session_complete=student_state.is_completed
                )
            
            else:
                # Handle failure
                if request.node_id not in student_state.failed_attempts:
                    student_state.failed_attempts[request.node_id] = 0
                student_state.failed_attempts[request.node_id] += 1
                
                db.add(student_state)
                db.commit()
                
                # Get hints if available
                hints = []
                if bubble_node.hints and student_state.failed_attempts[request.node_id] <= len(bubble_node.hints):
                    hint_index = student_state.failed_attempts[request.node_id] - 1
                    hints = [bubble_node.hints[hint_index]]
                
                # Log failure
                self._log_event(db, student_id, session_id, "bubble_failed", {
                    "node_id": request.node_id,
                    "attempt_number": student_state.failed_attempts[request.node_id],
                    "response": request.student_response[:100]  # Truncate for privacy
                })
                
                return BubbleAdvanceResponse(
                    success=False,
                    feedback=feedback,
                    hints_available=hints
                )
                
        except Exception as e:
            logger.error(f"Error advancing bubble: {e}")
            db.rollback()
            raise
    
    def get_student_state(self, student_id: int, session_id: int, db: Session) -> Optional[StudentStateResponse]:
        """Get current student state for a session"""
        stmt = select(StudentState).where(
            StudentState.student_id == student_id,
            StudentState.session_id == session_id
        )
        state = db.exec(stmt).first()
        
        if not state:
            return None
        
        return StudentStateResponse.from_orm(state)
    
    def get_session_analytics(self, session_id: int, db: Session) -> Dict[str, Any]:
        """Get analytics for a session"""
        try:
            # Get all student states for this session
            stmt = select(StudentState).where(StudentState.session_id == session_id)
            states = db.exec(stmt).all()
            
            if not states:
                return {"error": "No student data found"}
            
            # Calculate metrics
            total_students = len(states)
            completed_students = len([s for s in states if s.is_completed])
            completion_rate = (completed_students / total_students) * 100 if total_students > 0 else 0
            
            # Average metrics for completed sessions only
            completed_states = [s for s in states if s.is_completed]
            avg_completion_time = 0
            avg_coins = 0
            
            if completed_states:
                avg_completion_time = sum(s.total_time_spent for s in completed_states) / len(completed_states)
                avg_coins = sum(s.total_coins for s in completed_states) / len(completed_states)
            
            # Most challenging bubbles (highest failure rate)
            all_failures = {}
            for state in states:
                for node_id, attempts in state.failed_attempts.items():
                    if node_id not in all_failures:
                        all_failures[node_id] = []
                    all_failures[node_id].append(attempts)
            
            challenging_bubbles = []
            for node_id, attempts_list in all_failures.items():
                avg_attempts = sum(attempts_list) / len(attempts_list)
                if avg_attempts > 1.5:  # More than 1.5 attempts on average
                    challenging_bubbles.append({
                        "node_id": node_id,
                        "avg_attempts": round(avg_attempts, 2),
                        "students_struggled": len(attempts_list)
                    })
            
            challenging_bubbles.sort(key=lambda x: x["avg_attempts"], reverse=True)
            
            return {
                "total_students": total_students,
                "completed_students": completed_students,
                "completion_rate": round(completion_rate, 2),
                "avg_completion_time_minutes": round(avg_completion_time / 60, 2),
                "avg_coins_earned": round(avg_coins, 2),
                "challenging_bubbles": challenging_bubbles[:5],  # Top 5 most challenging
                "student_states": [
                    {
                        "student_id": s.student_id,
                        "completion_percentage": s.completion_percentage,
                        "total_coins": s.total_coins,
                        "is_completed": s.is_completed,
                        "time_spent_minutes": round(s.total_time_spent / 60, 2)
                    }
                    for s in states
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {"error": str(e)}
    
    def _evaluate_response(self, bubble_node: BubbleNode, response: str, code_output: Optional[str] = None) -> Tuple[bool, str, int]:
        """Evaluate student response for a bubble"""
        try:
            if bubble_node.type == "concept":
                # Concept bubbles - simple acknowledgment
                if len(response.strip()) > 0:
                    return True, "Great! You've reviewed the concept.", bubble_node.coin_reward
                else:
                    return False, "Please acknowledge that you've read the concept.", 0
            
            elif bubble_node.type == "quiz":
                # Quiz evaluation - simplified for now
                if bubble_node.expected_output and response.strip().lower() == bubble_node.expected_output.lower():
                    return True, "Correct answer!", bubble_node.coin_reward
                else:
                    return False, "That's not quite right. Try again!", 0
            
            elif bubble_node.type == "task":
                # Code task evaluation
                if bubble_node.expected_output and code_output:
                    if code_output.strip() == bubble_node.expected_output.strip():
                        return True, "Perfect! Your code works correctly.", bubble_node.coin_reward
                    else:
                        return False, f"Output doesn't match. Expected: {bubble_node.expected_output}, Got: {code_output}", 0
                elif len(response.strip()) > 10:  # Minimum effort check
                    return True, "Good effort! Your solution has been submitted.", bubble_node.coin_reward
                else:
                    return False, "Please provide a more complete solution.", 0
            
            else:
                # Default case
                return True, "Response recorded.", bubble_node.coin_reward
                
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return False, "Error evaluating your response. Please try again.", 0
    
    def _award_coins(self, db: Session, student_id: int, session_id: int, amount: int, description: str):
        """Award coins to student"""
        try:
            transaction = CoinTransaction(
                student_id=student_id,
                session_id=session_id,
                amount=amount,
                transaction_type="earned",
                description=description,
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error awarding coins: {e}")
    
    def _log_event(self, db: Session, student_id: int, session_id: int, event_type: str, metadata: Dict[str, Any]):
        """Log student event"""
        try:
            event = EventLog(
                student_id=student_id,
                session_id=session_id,
                event_type=event_type,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            db.add(event)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def get_student_progress(self, student_id: int, db: Session) -> Dict[str, Any]:
        """Get overall student progress across all sessions"""
        try:
            # Get all student states
            stmt = select(StudentState).where(StudentState.student_id == student_id)
            states = db.exec(stmt).all()
            
            # Get total coins
            coin_stmt = select(CoinTransaction).where(CoinTransaction.student_id == student_id)
            transactions = db.exec(coin_stmt).all()
            total_coins = sum(t.amount for t in transactions if t.transaction_type == "earned")
            
            # Calculate progress
            total_sessions = len(states)
            completed_sessions = len([s for s in states if s.is_completed])
            total_time_spent = sum(s.total_time_spent for s in states)
            
            return {
                "student_id": student_id,
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
                "total_coins": total_coins,
                "total_time_spent_hours": round(total_time_spent / 3600, 2),
                "avg_session_time_minutes": round(total_time_spent / total_sessions / 60, 2) if total_sessions > 0 else 0,
                "recent_sessions": [
                    {
                        "session_id": s.session_id,
                        "completion_percentage": s.completion_percentage,
                        "coins_earned": s.total_coins,
                        "is_completed": s.is_completed,
                        "last_activity": s.last_activity_at.isoformat()
                    }
                    for s in sorted(states, key=lambda x: x.last_activity_at, reverse=True)[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting student progress: {e}")
            return {"error": str(e)} 