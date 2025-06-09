"""
Learning Graph Service - Manages curriculum structure and learning paths
"""
import asyncio
from typing import List, Dict, Optional, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import json

from app.database import SessionLocal
from app.models.learning_graph import (
    LearningConcept, ConceptPrerequisite, StudentProgress, 
    LearningPath, AssessmentResult, DifficultyLevel, PrerequisiteType
)

class LearningGraphService:
    """Service for managing learning concepts, prerequisites, and paths"""
    
    def __init__(self):
        self.db_session = None
    
    def get_db(self) -> Session:
        """Get database session"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session
    
    async def get_concept_by_slug(self, slug: str) -> Optional[Dict]:
        """Get learning concept by slug"""
        db = self.get_db()
        concept = db.query(LearningConcept).filter(
            LearningConcept.slug == slug,
            LearningConcept.is_active == True
        ).first()
        
        if concept:
            return {
                "id": concept.id,
                "name": concept.name,
                "slug": concept.slug,
                "description": concept.description,
                "difficulty_level": concept.difficulty_level,
                "estimated_time_minutes": concept.estimated_time_minutes,
                "category": concept.category,
                "learning_objectives": concept.learning_objectives,
                "code_examples": concept.code_examples,
                "practice_exercises": concept.practice_exercises,
                "mastery_threshold": concept.mastery_threshold
            }
        return None
    
    async def get_prerequisites(self, concept_id: int) -> List[Dict]:
        """Get prerequisites for a concept"""
        db = self.get_db()
        prerequisites = db.query(ConceptPrerequisite).filter(
            ConceptPrerequisite.concept_id == concept_id
        ).all()
        
        result = []
        for prereq in prerequisites:
            prereq_concept = db.query(LearningConcept).filter(
                LearningConcept.id == prereq.prerequisite_id
            ).first()
            
            if prereq_concept:
                result.append({
                    "concept_id": prereq_concept.id,
                    "name": prereq_concept.name,
                    "slug": prereq_concept.slug,
                    "prerequisite_type": prereq.prerequisite_type,
                    "strength": prereq.strength
                })
        
        return result
    
    async def check_prerequisites_met(self, concept_id: int, session_id: str, user_id: str) -> Dict:
        """Check if student has met prerequisites for a concept"""
        prerequisites = await self.get_prerequisites(concept_id)
        db = self.get_db()
        
        met_prerequisites = []
        missing_prerequisites = []
        
        for prereq in prerequisites:
            progress = db.query(StudentProgress).filter(
                and_(
                    StudentProgress.session_id == session_id,
                    StudentProgress.user_id == user_id,
                    StudentProgress.concept_id == prereq["concept_id"]
                )
            ).first()
            
            # Check if prerequisite is met based on type
            is_met = False
            if progress:
                if prereq["prerequisite_type"] == PrerequisiteType.HARD.value:
                    # Hard prerequisite requires mastery
                    is_met = progress.status == "mastered"
                elif prereq["prerequisite_type"] == PrerequisiteType.SOFT.value:
                    # Soft prerequisite requires some progress
                    is_met = progress.mastery_score >= 0.5
                else:  # REINFORCEMENT
                    # Reinforcement can be learned together
                    is_met = True
            
            if is_met:
                met_prerequisites.append(prereq)
            else:
                missing_prerequisites.append(prereq)
        
        return {
            "all_met": len(missing_prerequisites) == 0,
            "met": met_prerequisites,
            "missing": missing_prerequisites,
            "total_prerequisites": len(prerequisites)
        }
    
    async def get_next_recommended_concepts(self, session_id: str, user_id: str, limit: int = 3) -> List[Dict]:
        """Get next recommended concepts based on current progress"""
        db = self.get_db()
        
        # Get current progress
        current_progress = db.query(StudentProgress).filter(
            and_(
                StudentProgress.session_id == session_id,
                StudentProgress.user_id == user_id
            )
        ).all()
        
        # Get concepts student has mastered
        mastered_concept_ids = [
            p.concept_id for p in current_progress 
            if p.status == "mastered"
        ]
        
        # Get concepts student is working on
        in_progress_concept_ids = [
            p.concept_id for p in current_progress 
            if p.status == "in_progress"
        ]
        
        # Find concepts where prerequisites are met
        all_concepts = db.query(LearningConcept).filter(
            LearningConcept.is_active == True
        ).all()
        
        recommendations = []
        
        for concept in all_concepts:
            # Skip if already mastered or in progress
            if concept.id in mastered_concept_ids or concept.id in in_progress_concept_ids:
                continue
            
            # Check prerequisites
            prereq_check = await self.check_prerequisites_met(
                concept.id, session_id, user_id
            )
            
            if prereq_check["all_met"]:
                recommendations.append({
                    "id": concept.id,
                    "name": concept.name,
                    "slug": concept.slug,
                    "description": concept.description,
                    "difficulty_level": concept.difficulty_level,
                    "estimated_time_minutes": concept.estimated_time_minutes,
                    "category": concept.category,
                    "reason": "Prerequisites met"
                })
        
        # Sort by difficulty and return top recommendations
        recommendations.sort(key=lambda x: x["difficulty_level"])
        return recommendations[:limit]
    
    async def update_student_progress(
        self, 
        session_id: str, 
        user_id: str, 
        concept_id: int, 
        mastery_delta: float,
        time_spent_minutes: int = 0,
        confidence_level: Optional[float] = None
    ) -> Dict:
        """Update student progress for a concept"""
        db = self.get_db()
        
        # Get or create progress record
        progress = db.query(StudentProgress).filter(
            and_(
                StudentProgress.session_id == session_id,
                StudentProgress.user_id == user_id,
                StudentProgress.concept_id == concept_id
            )
        ).first()
        
        if not progress:
            progress = StudentProgress(
                session_id=session_id,
                user_id=user_id,
                concept_id=concept_id,
                first_introduced_at=datetime.utcnow()
            )
            db.add(progress)
        
        # Update progress metrics
        progress.mastery_score = min(1.0, max(0.0, progress.mastery_score + mastery_delta))
        progress.time_spent_minutes += time_spent_minutes
        progress.attempts_count += 1
        progress.last_practiced_at = datetime.utcnow()
        
        if confidence_level is not None:
            progress.confidence_level = confidence_level
        
        # Update status based on mastery score
        concept = db.query(LearningConcept).filter(
            LearningConcept.id == concept_id
        ).first()
        
        if concept and progress.mastery_score >= concept.mastery_threshold:
            progress.status = "mastered"
            if not progress.mastered_at:
                progress.mastered_at = datetime.utcnow()
        elif progress.mastery_score > 0.1:
            progress.status = "in_progress"
        else:
            progress.status = "not_started"
        
        db.commit()
        
        return {
            "concept_id": concept_id,
            "mastery_score": progress.mastery_score,
            "status": progress.status,
            "confidence_level": progress.confidence_level,
            "time_spent": progress.time_spent_minutes,
            "attempts": progress.attempts_count
        }
    
    async def get_learning_path(self, session_id: str, user_id: str) -> Optional[Dict]:
        """Get current learning path for student"""
        db = self.get_db()
        
        path = db.query(LearningPath).filter(
            and_(
                LearningPath.session_id == session_id,
                LearningPath.user_id == user_id,
                LearningPath.status == "active"
            )
        ).first()
        
        if path:
            return {
                "id": path.id,
                "name": path.name,
                "description": path.description,
                "goal": path.goal,
                "concept_sequence": path.concept_sequence,
                "current_position": path.current_position,
                "completion_percentage": path.completion_percentage,
                "estimated_completion_hours": path.estimated_completion_hours,
                "actual_time_spent_minutes": path.actual_time_spent_minutes
            }
        
        return None
    
    async def create_personalized_path(
        self, 
        session_id: str, 
        user_id: str, 
        goal: str,
        difficulty_preference: float = 0.5,
        topics: List[str] = None
    ) -> Dict:
        """Create a personalized learning path for student"""
        db = self.get_db()
        
        # Get available concepts based on topics or default to Python basics
        if topics is None:
            topics = ["python-basics", "data-structures", "control-flow"]
        
        concepts = db.query(LearningConcept).filter(
            and_(
                LearningConcept.category.in_(topics),
                LearningConcept.is_active == True
            )
        ).order_by(LearningConcept.difficulty_level).all()
        
        # Build optimal sequence considering prerequisites
        concept_sequence = await self._build_optimal_sequence(concepts)
        
        # Create learning path
        path = LearningPath(
            session_id=session_id,
            user_id=user_id,
            name=f"Personalized Path: {goal}",
            description=f"Custom learning path focused on: {', '.join(topics)}",
            goal=goal,
            concept_sequence=concept_sequence,
            difficulty_preference=difficulty_preference,
            estimated_completion_hours=len(concept_sequence) * 0.5  # 30 min per concept
        )
        
        db.add(path)
        db.commit()
        
        return {
            "path_id": path.id,
            "name": path.name,
            "concept_count": len(concept_sequence),
            "estimated_hours": path.estimated_completion_hours,
            "first_concept": concept_sequence[0] if concept_sequence else None
        }
    
    async def _build_optimal_sequence(self, concepts: List[LearningConcept]) -> List[int]:
        """Build optimal learning sequence considering prerequisites"""
        concept_map = {c.id: c for c in concepts}
        sequence = []
        remaining = set(concept_map.keys())
        
        while remaining:
            # Find concepts with no remaining prerequisites
            available = []
            for concept_id in remaining:
                prereqs = await self.get_prerequisites(concept_id)
                prereq_ids = [p["concept_id"] for p in prereqs 
                             if p["prerequisite_type"] == PrerequisiteType.HARD.value]
                
                # Check if all hard prerequisites are already in sequence
                if all(pid in sequence for pid in prereq_ids):
                    available.append(concept_id)
            
            if not available:
                # Break circular dependencies by taking lowest difficulty
                available = [min(remaining, key=lambda cid: concept_map[cid].difficulty_level)]
            
            # Sort available by difficulty and take the easiest
            available.sort(key=lambda cid: concept_map[cid].difficulty_level)
            next_concept = available[0]
            
            sequence.append(next_concept)
            remaining.remove(next_concept)
        
        return sequence
    
    async def advance_learning_path(self, session_id: str, user_id: str) -> Dict:
        """Advance student to next concept in their learning path"""
        db = self.get_db()
        
        path = db.query(LearningPath).filter(
            and_(
                LearningPath.session_id == session_id,
                LearningPath.user_id == user_id,
                LearningPath.status == "active"
            )
        ).first()
        
        if not path:
            return {"error": "No active learning path found"}
        
        # Check if current concept is mastered
        if path.current_position < len(path.concept_sequence):
            current_concept_id = path.concept_sequence[path.current_position]
            
            progress = db.query(StudentProgress).filter(
                and_(
                    StudentProgress.session_id == session_id,
                    StudentProgress.user_id == user_id,
                    StudentProgress.concept_id == current_concept_id
                )
            ).first()
            
            if progress and progress.status == "mastered":
                # Advance to next concept
                path.current_position += 1
                path.completion_percentage = (path.current_position / len(path.concept_sequence)) * 100
                
                db.commit()
                
                if path.current_position >= len(path.concept_sequence):
                    path.status = "completed"
                    db.commit()
                    
                    return {
                        "status": "path_completed",
                        "message": "Congratulations! You've completed your learning path!",
                        "completion_percentage": 100
                    }
                else:
                    next_concept_id = path.concept_sequence[path.current_position]
                    next_concept = db.query(LearningConcept).filter(
                        LearningConcept.id == next_concept_id
                    ).first()
                    
                    return {
                        "status": "advanced",
                        "next_concept": {
                            "id": next_concept.id,
                            "name": next_concept.name,
                            "slug": next_concept.slug
                        },
                        "completion_percentage": path.completion_percentage
                    }
        
        return {"status": "no_advancement", "message": "Current concept not yet mastered"}
    
    async def get_curriculum_summary(self) -> Dict:
        """Get summary of current curriculum in database"""
        db = self.get_db()
        
        try:
            concepts = db.query(LearningConcept).all()
            prerequisites = db.query(ConceptPrerequisite).all()
            
            concept_summary = []
            for concept in concepts:
                concept_summary.append({
                    "id": concept.id,
                    "name": concept.name,
                    "slug": concept.slug,
                    "category": concept.category,
                    "difficulty": concept.difficulty_level,
                    "estimated_time": concept.estimated_time_minutes
                })
            
            prerequisite_summary = []
            for prereq in prerequisites:
                concept_name = db.query(LearningConcept).filter(
                    LearningConcept.id == prereq.concept_id
                ).first().name
                
                prerequisite_name = db.query(LearningConcept).filter(
                    LearningConcept.id == prereq.prerequisite_id
                ).first().name
                
                prerequisite_summary.append({
                    "concept": concept_name,
                    "prerequisite": prerequisite_name,
                    "type": prereq.prerequisite_type,
                    "strength": prereq.strength
                })
            
            return {
                "concepts_count": len(concepts),
                "prerequisites_count": len(prerequisites),
                "concepts": concept_summary,
                "prerequisites": prerequisite_summary
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get curriculum summary: {str(e)}"
            }
    
    def close(self):
        """Close database session"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None 