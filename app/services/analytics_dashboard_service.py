"""
Analytics Dashboard Service - Provides data for frontend analytics visualizations
Serves learning journey maps, performance analytics, and curriculum insights
"""
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import json
import statistics
from collections import defaultdict

from app.database import SessionLocal
from app.models.learning_graph import (
    LearningConcept, ConceptPrerequisite, StudentProgress, 
    LearningPath, AssessmentResult, DifficultyLevel
)
from app.models.session import LearningSession, ConversationLog, LearningMetrics
from app.services.learning_analytics_service import LearningAnalyticsService, LearningPattern, EngagementLevel

class AnalyticsDashboardService:
    """Service for providing analytics dashboard data to frontend"""
    
    def __init__(self):
        self.db_session = None
        self.analytics_service = LearningAnalyticsService()
    
    def get_db(self) -> Session:
        """Get database session"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session
    
    async def get_learning_journey_map(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Generate interactive learning journey visualization data"""
        db = self.get_db()
        
        # Get all concepts and their relationships
        concepts = db.query(LearningConcept).filter(LearningConcept.is_active == True).all()
        prerequisites = db.query(ConceptPrerequisite).all()
        progress_data = await self.analytics_service._get_progress_data(session_id, user_id)
        
        # Build progress lookup
        progress_lookup = {p.concept_id: p for p in progress_data}
        
        # Create nodes for visualization
        nodes = []
        for concept in concepts:
            progress = progress_lookup.get(concept.id)
            status = progress.status if progress else "not_started"
            mastery_score = progress.mastery_score if progress else 0.0
            
            nodes.append({
                "id": concept.id,
                "name": concept.name,
                "slug": concept.slug,
                "category": concept.category,
                "difficulty_level": concept.difficulty_level,
                "estimated_time_minutes": concept.estimated_time_minutes,
                "status": status,
                "mastery_score": mastery_score,
                "confidence_level": progress.confidence_level if progress else 0.5,
                "time_spent_minutes": progress.time_spent_minutes if progress else 0,
                "position": self._calculate_node_position(concept, concepts, prerequisites)
            })
        
        # Create edges for prerequisites
        edges = []
        for prereq in prerequisites:
            edges.append({
                "source": prereq.prerequisite_id,
                "target": prereq.concept_id,
                "type": prereq.prerequisite_type,
                "strength": prereq.strength
            })
        
        # Calculate learning path
        current_path = await self._get_recommended_learning_sequence(session_id, user_id)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "current_path": current_path,
            "statistics": {
                "total_concepts": len(concepts),
                "concepts_started": len([n for n in nodes if n["status"] != "not_started"]),
                "concepts_mastered": len([n for n in nodes if n["status"] == "mastered"]),
                "total_time_spent_hours": sum(n["time_spent_minutes"] for n in nodes) / 60,
                "average_mastery_score": statistics.mean([n["mastery_score"] for n in nodes if n["mastery_score"] > 0]) if any(n["mastery_score"] > 0 for n in nodes) else 0
            }
        }
    
    def _calculate_node_position(self, concept: LearningConcept, all_concepts: List[LearningConcept], prerequisites: List[ConceptPrerequisite]) -> Dict[str, float]:
        """Calculate node position for graph visualization"""
        # Simple layout algorithm - in practice, you'd use more sophisticated graph layout
        category_positions = {
            "python-basics": {"x": 100, "y": 100},
            "data-structures": {"x": 300, "y": 100},
            "control-flow": {"x": 200, "y": 200},
            "functions": {"x": 400, "y": 200},
            "oop": {"x": 500, "y": 300},
            "advanced": {"x": 600, "y": 400}
        }
        
        base_pos = category_positions.get(concept.category, {"x": 300, "y": 300})
        
        # Add some jitter based on difficulty level
        x_offset = (concept.difficulty_level - 3) * 50
        y_offset = concept.id % 3 * 40  # Simple spread
        
        return {
            "x": base_pos["x"] + x_offset,
            "y": base_pos["y"] + y_offset
        }
    
    async def _get_recommended_learning_sequence(self, session_id: str, user_id: str) -> List[int]:
        """Get recommended sequence of concept IDs for learning path"""
        db = self.get_db()
        
        # Get current learning path
        learning_path = db.query(LearningPath).filter(
            and_(
                LearningPath.session_id == session_id,
                LearningPath.user_id == user_id,
                LearningPath.status == "active"
            )
        ).first()
        
        if learning_path and learning_path.concept_sequence:
            return learning_path.concept_sequence
        
        # If no path exists, create a basic recommended sequence
        progress_data = await self.analytics_service._get_progress_data(session_id, user_id)
        mastered_ids = [p.concept_id for p in progress_data if p.status == "mastered"]
        
        # Get unmastered concepts, ordered by difficulty
        unmastered_concepts = db.query(LearningConcept).filter(
            and_(
                LearningConcept.is_active == True,
                ~LearningConcept.id.in_(mastered_ids)
            )
        ).order_by(LearningConcept.difficulty_level).limit(10).all()
        
        return [c.id for c in unmastered_concepts]
    
    async def get_performance_analytics(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance analytics"""
        progress_data = await self.analytics_service._get_progress_data(session_id, user_id)
        conversation_data = await self.analytics_service._get_conversation_data(session_id, user_id)
        
        if not progress_data:
            return {"error": "No progress data available"}
        
        # Time series data for progress tracking
        time_series = []
        cumulative_mastery = 0
        
        progress_by_date = defaultdict(list)
        for progress in progress_data:
            if progress.mastered_at:
                date_key = progress.mastered_at.date().isoformat()
                progress_by_date[date_key].append(progress)
        
        for date_str in sorted(progress_by_date.keys()):
            cumulative_mastery += len(progress_by_date[date_str])
            time_series.append({
                "date": date_str,
                "concepts_mastered": len(progress_by_date[date_str]),
                "cumulative_mastery": cumulative_mastery,
                "daily_study_time": sum(p.time_spent_minutes for p in progress_by_date[date_str])
            })
        
        # Mastery score distribution
        mastery_scores = [p.mastery_score for p in progress_data if p.mastery_score > 0]
        mastery_distribution = {
            "excellent": len([s for s in mastery_scores if s >= 0.9]),
            "good": len([s for s in mastery_scores if 0.7 <= s < 0.9]),
            "satisfactory": len([s for s in mastery_scores if 0.5 <= s < 0.7]),
            "needs_improvement": len([s for s in mastery_scores if s < 0.5])
        }
        
        # Learning velocity by category
        category_performance = defaultdict(list)
        for progress in progress_data:
            if progress.concept and progress.concept.category:
                category_performance[progress.concept.category].append({
                    "mastery_score": progress.mastery_score,
                    "time_spent": progress.time_spent_minutes,
                    "status": progress.status
                })
        
        category_stats = {}
        for category, performances in category_performance.items():
            category_stats[category] = {
                "avg_mastery_score": statistics.mean([p["mastery_score"] for p in performances]),
                "avg_time_spent": statistics.mean([p["time_spent"] for p in performances]),
                "completion_rate": len([p for p in performances if p["status"] == "mastered"]) / len(performances)
            }
        
        # Difficulty level analysis
        difficulty_analysis = defaultdict(list)
        for progress in progress_data:
            if progress.concept:
                difficulty_analysis[progress.concept.difficulty_level].append(progress.mastery_score)
        
        difficulty_performance = {}
        for level, scores in difficulty_analysis.items():
            difficulty_performance[f"level_{level}"] = {
                "avg_score": statistics.mean(scores),
                "concept_count": len(scores),
                "mastery_rate": len([s for s in scores if s >= 0.75]) / len(scores)
            }
        
        # Engagement metrics over time
        engagement_timeline = []
        if conversation_data:
            conversations_by_date = defaultdict(list)
            for conv in conversation_data:
                date_key = conv.created_at.date().isoformat()
                conversations_by_date[date_key].append(conv)
            
            for date_str in sorted(conversations_by_date.keys()):
                daily_convs = conversations_by_date[date_str]
                engagement_timeline.append({
                    "date": date_str,
                    "interaction_count": len(daily_convs),
                    "avg_response_time": statistics.mean([c.response_latency for c in daily_convs if c.response_latency]) or 0,
                    "total_session_time": sum([(c.response_latency or 0) for c in daily_convs])
                })
        
        return {
            "time_series_progress": time_series,
            "mastery_distribution": mastery_distribution,
            "category_performance": category_stats,
            "difficulty_performance": difficulty_performance,
            "engagement_timeline": engagement_timeline,
            "summary_stats": {
                "total_concepts_attempted": len(progress_data),
                "concepts_mastered": len([p for p in progress_data if p.status == "mastered"]),
                "average_mastery_score": statistics.mean(mastery_scores) if mastery_scores else 0,
                "total_study_time_hours": sum(p.time_spent_minutes for p in progress_data) / 60,
                "learning_streak_days": len(set(p.last_practiced_at.date() for p in progress_data if p.last_practiced_at)) if any(p.last_practiced_at for p in progress_data) else 0,
                "favorite_category": max(category_stats.keys(), key=lambda k: category_stats[k]["avg_mastery_score"]) if category_stats else None
            }
        }
    
    async def get_concept_mastery_heatmap(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Generate concept mastery heatmap data"""
        db = self.get_db()
        progress_data = await self.analytics_service._get_progress_data(session_id, user_id)
        
        # Group concepts by category and difficulty
        concepts = db.query(LearningConcept).filter(LearningConcept.is_active == True).all()
        progress_lookup = {p.concept_id: p for p in progress_data}
        
        heatmap_data = []
        categories = set(c.category for c in concepts)
        difficulty_levels = list(range(1, 6))  # 1 to 5
        
        for category in categories:
            for difficulty in difficulty_levels:
                category_concepts = [c for c in concepts if c.category == category and c.difficulty_level == difficulty]
                
                if category_concepts:
                    mastery_scores = []
                    for concept in category_concepts:
                        progress = progress_lookup.get(concept.id)
                        if progress:
                            mastery_scores.append(progress.mastery_score)
                        else:
                            mastery_scores.append(0.0)
                    
                    avg_mastery = statistics.mean(mastery_scores)
                    
                    heatmap_data.append({
                        "category": category,
                        "difficulty_level": difficulty,
                        "avg_mastery_score": avg_mastery,
                        "concept_count": len(category_concepts),
                        "concepts_mastered": len([s for s in mastery_scores if s >= 0.75]),
                        "concepts": [
                            {
                                "id": c.id,
                                "name": c.name,
                                "mastery_score": progress_lookup.get(c.id).mastery_score if progress_lookup.get(c.id) else 0.0,
                                "status": progress_lookup.get(c.id).status if progress_lookup.get(c.id) else "not_started"
                            } for c in category_concepts
                        ]
                    })
        
        return {
            "heatmap_data": heatmap_data,
            "categories": list(categories),
            "difficulty_levels": difficulty_levels,
            "overall_mastery": statistics.mean([d["avg_mastery_score"] for d in heatmap_data]) if heatmap_data else 0
        }
    
    async def get_learning_recommendations(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get AI-powered learning recommendations"""
        # Use the analytics service to get comprehensive analysis
        student_profile = await self.analytics_service.analyze_student_profile(session_id, user_id)
        
        # Extract key recommendations
        high_priority_insights = [
            insight for insight in student_profile.get("insights", [])
            if insight["priority"] <= 2 and insight["actionable"]
        ]
        
        performance_predictions = student_profile.get("performance_predictions", [])
        personalization_recs = student_profile.get("personalization_recommendations", [])
        
        # Generate next steps
        next_steps = await self._generate_next_steps(session_id, user_id, student_profile)
        
        return {
            "priority_insights": high_priority_insights,
            "next_concepts": performance_predictions[:3],  # Top 3 upcoming concepts
            "study_recommendations": personalization_recs,
            "next_steps": next_steps,
            "learning_goals": await self._suggest_learning_goals(session_id, user_id, student_profile)
        }
    
    async def _generate_next_steps(self, session_id: str, user_id: str, profile: Dict) -> List[Dict[str, Any]]:
        """Generate specific next steps for the student"""
        next_steps = []
        
        learning_patterns = profile.get("profile", {}).get("learning_patterns", [])
        avg_mastery_rate = profile.get("profile", {}).get("average_mastery_rate", 0.0)
        
        # Based on mastery rate
        if avg_mastery_rate < 0.5:
            next_steps.append({
                "action": "review_fundamentals",
                "title": "Review Fundamental Concepts",
                "description": "Focus on mastering basic concepts before advancing",
                "estimated_time": "2-3 hours",
                "priority": "high"
            })
        elif avg_mastery_rate > 0.8:
            next_steps.append({
                "action": "advance_difficulty",
                "title": "Take on Advanced Challenges",
                "description": "You're ready for more challenging concepts",
                "estimated_time": "1-2 hours",
                "priority": "medium"
            })
        
        # Based on learning patterns
        if "visual_learner" in learning_patterns:
            next_steps.append({
                "action": "explore_visualizations",
                "title": "Explore Visual Learning Materials",
                "description": "Look for diagrams, charts, and visual explanations",
                "estimated_time": "30 minutes",
                "priority": "medium"
            })
        
        if "needs_repetition" in learning_patterns:
            next_steps.append({
                "action": "practice_exercises",
                "title": "Complete Practice Exercises",
                "description": "Reinforce learning through additional practice",
                "estimated_time": "1 hour",
                "priority": "high"
            })
        
        return next_steps
    
    async def _suggest_learning_goals(self, session_id: str, user_id: str, profile: Dict) -> List[Dict[str, Any]]:
        """Suggest personalized learning goals"""
        goals = []
        
        concepts_mastered = profile.get("profile", {}).get("concepts_mastered", 0)
        total_concepts = profile.get("profile", {}).get("total_concepts_studied", 0)
        
        # Short-term goals
        if concepts_mastered < 5:
            goals.append({
                "type": "short_term",
                "title": "Master Your First 5 Concepts",
                "description": "Build a strong foundation with 5 core concepts",
                "target_value": 5,
                "current_value": concepts_mastered,
                "deadline": "1 week"
            })
        else:
            goals.append({
                "type": "short_term",
                "title": f"Master {concepts_mastered + 3} Concepts",
                "description": "Continue building your knowledge base",
                "target_value": concepts_mastered + 3,
                "current_value": concepts_mastered,
                "deadline": "2 weeks"
            })
        
        # Medium-term goals
        goals.append({
            "type": "medium_term",
            "title": "Achieve 80% Average Mastery",
            "description": "Maintain high understanding across all topics",
            "target_value": 0.8,
            "current_value": profile.get("profile", {}).get("average_mastery_rate", 0.0),
            "deadline": "1 month"
        })
        
        # Long-term goals
        goals.append({
            "type": "long_term",
            "title": "Complete Learning Path",
            "description": "Master all concepts in your chosen learning path",
            "target_value": 100,
            "current_value": (concepts_mastered / max(total_concepts, 1)) * 100,
            "deadline": "3 months"
        })
        
        return goals
    
    async def get_engagement_insights(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get detailed engagement analysis"""
        engagement_data = await self.analytics_service._analyze_engagement_patterns(session_id, user_id)
        conversation_data = await self.analytics_service._get_conversation_data(session_id, user_id)
        
        # Calculate engagement trends
        if conversation_data:
            recent_conversations = conversation_data[-10:]  # Last 10 conversations
            older_conversations = conversation_data[:-10] if len(conversation_data) > 10 else []
            
            recent_avg_response_time = statistics.mean([c.response_latency for c in recent_conversations if c.response_latency]) or 0
            older_avg_response_time = statistics.mean([c.response_latency for c in older_conversations if c.response_latency]) or recent_avg_response_time
            
            engagement_trend = "improving" if recent_avg_response_time < older_avg_response_time else "declining"
        else:
            engagement_trend = "stable"
        
        return {
            "current_engagement": engagement_data,
            "trend": engagement_trend,
            "recommendations": [
                "Take short breaks between learning sessions",
                "Try switching between different types of content",
                "Set small, achievable daily goals",
                "Celebrate your progress milestones"
            ],
            "engagement_boosters": [
                {"activity": "Interactive coding exercises", "effectiveness": 0.9},
                {"activity": "Visual diagrams and explanations", "effectiveness": 0.8},
                {"activity": "Real-world examples", "effectiveness": 0.85},
                {"activity": "Progress celebrations", "effectiveness": 0.7}
            ]
        }
    
    def close(self):
        """Close database connections"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None
        self.analytics_service.close() 