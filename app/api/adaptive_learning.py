"""
Adaptive Learning API - Provides personalized learning support
Features dynamic content generation, performance-based hints, and adaptive feedback
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import Dict, List, Optional, Any
import logging

from app.database import get_db
from app.models.session import LearningSession, BubbleNode
from app.models.analytics import EventLog, EventType
from app.schemas.adaptive_learning import (
    AdaptiveContentRequest,
    AdaptiveContentResponse,
    HintRequest,
    HintResponse,
    PerformanceAnalysisRequest,
    PerformanceAnalysisResponse,
    LearningPathRecommendation
)
from app.services.bubble_evaluation_service import BubbleEvaluationService
from app.services.ai_tutor_service import AITutorService
from app.services.student_tracking_service import StudentTrackingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/adaptive-learning", tags=["adaptive-learning"])

# Initialize services
evaluation_service = BubbleEvaluationService()
ai_tutor_service = AITutorService()
tracking_service = StudentTrackingService()


@router.post("/content/generate", response_model=AdaptiveContentResponse)
async def generate_adaptive_content(
    request: AdaptiveContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate adaptive content based on student performance and learning style
    """
    try:
        # Get session and student context
        session = db.get(LearningSession, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Analyze student performance patterns
        performance_analysis = await analyze_student_performance(
            request.session_id, request.student_id, db
        )
        
        # Generate content based on performance and request type
        adaptive_content = await generate_content_for_performance(
            request, performance_analysis, db
        )
        
        # Track content generation
        background_tasks.add_task(
            track_adaptive_content_generation,
            request.session_id,
            request.content_type,
            adaptive_content,
            db
        )
        
        return AdaptiveContentResponse(
            content=adaptive_content,
            difficulty_level=determine_difficulty_level(performance_analysis),
            estimated_time=calculate_estimated_time(adaptive_content, performance_analysis),
            learning_objectives=extract_learning_objectives(request.content_type),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating adaptive content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hints/request", response_model=HintResponse)
async def request_hint(
    request: HintRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Provide contextual hints based on current student progress
    """
    try:
        # Get current bubble and student state
        session = db.get(LearningSession, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Analyze current struggle points
        struggle_analysis = await analyze_student_struggles(
            request.session_id, request.bubble_id, request.context, db
        )
        
        # Generate progressive hints
        hints = await generate_progressive_hints(
            request, struggle_analysis, db
        )
        
        # Track hint usage
        background_tasks.add_task(
            track_hint_usage,
            request.session_id,
            request.bubble_id,
            request.hint_level,
            db
        )
        
        return HintResponse(
            hint=hints[request.hint_level],
            hint_level=request.hint_level,
            max_hints_available=len(hints),
            next_hint_available=request.hint_level < len(hints) - 1,
            encouragement=generate_encouragement(struggle_analysis),
            related_resources=find_related_resources(request.bubble_id, db),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error generating hint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/analyze", response_model=PerformanceAnalysisResponse)
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze student performance patterns and provide insights
    """
    try:
        # Get comprehensive performance data
        performance_data = await get_comprehensive_performance_data(
            request.session_id, request.student_id, request.time_period, db
        )
        
        # Analyze learning patterns
        learning_patterns = await analyze_learning_patterns(performance_data)
        
        # Identify strengths and weaknesses
        strengths_weaknesses = await identify_strengths_weaknesses(performance_data)
        
        # Generate recommendations
        recommendations = await generate_learning_recommendations(
            performance_data, learning_patterns, strengths_weaknesses, db
        )
        
        return PerformanceAnalysisResponse(
            overall_progress=calculate_overall_progress(performance_data),
            learning_patterns=learning_patterns,
            strengths=strengths_weaknesses['strengths'],
            areas_for_improvement=strengths_weaknesses['weaknesses'],
            recommendations=recommendations,
            time_analysis=analyze_time_patterns(performance_data),
            difficulty_progression=analyze_difficulty_progression(performance_data),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error analyzing performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path/recommend/{session_id}", response_model=List[LearningPathRecommendation])
async def recommend_learning_path(
    session_id: str,
    student_id: Optional[str] = None,
    max_recommendations: int = 5,
    db: Session = Depends(get_db)
):
    """
    Recommend optimal learning path based on student progress and preferences
    """
    try:
        # Get session context
        session = db.get(LearningSession, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Analyze current progress
        current_progress = await get_session_progress(session_id, db)
        
        # Get student learning profile
        learning_profile = await get_student_learning_profile(student_id, db) if student_id else None
        
        # Generate path recommendations
        recommendations = await generate_path_recommendations(
            session, current_progress, learning_profile, max_recommendations, db
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error recommending learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def analyze_student_performance(
    session_id: str, 
    student_id: str, 
    db: Session
) -> Dict[str, Any]:
    """Analyze student performance patterns"""
    
    # Get performance metrics from database
    performance_data = await tracking_service.get_student_analytics(student_id, session_id, db)
    
    # Calculate key metrics
    analysis = {
        'completion_rate': performance_data.get('completion_rate', 0.0),
        'average_score': performance_data.get('average_score', 0.0),
        'time_efficiency': performance_data.get('time_efficiency', 1.0),
        'struggle_areas': performance_data.get('common_mistakes', []),
        'learning_pace': performance_data.get('learning_pace', 'medium'),
        'preferred_content_types': performance_data.get('preferred_types', ['concept']),
        'hint_usage_pattern': performance_data.get('hint_usage', 'moderate')
    }
    
    return analysis


async def generate_content_for_performance(
    request: AdaptiveContentRequest,
    performance_analysis: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Generate content adapted to student performance"""
    
    content_generators = {
        'concept': generate_adaptive_concept_content,
        'task': generate_adaptive_task_content,
        'quiz': generate_adaptive_quiz_content,
        'example': generate_adaptive_example_content,
        'explanation': generate_adaptive_explanation_content
    }
    
    generator = content_generators.get(request.content_type)
    if not generator:
        raise ValueError(f"Unsupported content type: {request.content_type}")
    
    return await generator(request, performance_analysis, db)


async def generate_adaptive_concept_content(
    request: AdaptiveContentRequest,
    performance_analysis: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Generate adaptive concept content"""
    
    # Adjust complexity based on performance
    complexity_level = 'basic' if performance_analysis['average_score'] < 70 else \
                      'advanced' if performance_analysis['average_score'] > 85 else 'intermediate'
    
    # Adjust content style based on preferences
    preferred_style = performance_analysis.get('preferred_content_types', ['text'])[0]
    
    content = {
        'title': f"Adaptive Concept: {request.topic}",
        'complexity': complexity_level,
        'content_style': preferred_style,
        'main_content': await generate_concept_text(request.topic, complexity_level),
        'examples': await generate_concept_examples(request.topic, complexity_level),
        'key_points': await extract_key_points(request.topic, complexity_level),
        'interactive_elements': await generate_interactive_elements(request.topic, preferred_style)
    }
    
    return content


async def generate_adaptive_task_content(
    request: AdaptiveContentRequest,
    performance_analysis: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Generate adaptive task content"""
    
    # Adjust difficulty based on recent performance
    if performance_analysis['completion_rate'] < 0.6:
        difficulty = 'beginner'
        scaffolding_level = 'high'
    elif performance_analysis['completion_rate'] > 0.8:
        difficulty = 'intermediate'
        scaffolding_level = 'low'
    else:
        difficulty = 'beginner-intermediate'
        scaffolding_level = 'medium'
    
    content = {
        'title': f"Adaptive Task: {request.topic}",
        'difficulty': difficulty,
        'scaffolding_level': scaffolding_level,
        'instructions': await generate_task_instructions(request.topic, difficulty, scaffolding_level),
        'starter_code': await generate_starter_code(request.topic, scaffolding_level),
        'test_cases': await generate_test_cases(request.topic, difficulty),
        'hints': await generate_task_hints(request.topic, performance_analysis),
        'success_criteria': await define_success_criteria(request.topic, difficulty)
    }
    
    return content


async def generate_adaptive_quiz_content(
    request: AdaptiveContentRequest,
    performance_analysis: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Generate adaptive quiz content"""
    
    # Adjust question types based on strengths/weaknesses
    weak_areas = performance_analysis.get('struggle_areas', [])
    strong_areas = ['general'] if not weak_areas else []
    
    content = {
        'title': f"Adaptive Quiz: {request.topic}",
        'question_count': 5 if performance_analysis['completion_rate'] > 0.7 else 3,
        'difficulty_distribution': calculate_difficulty_distribution(performance_analysis),
        'focus_areas': weak_areas if weak_areas else [request.topic],
        'questions': await generate_quiz_questions(request.topic, weak_areas, performance_analysis),
        'feedback_style': 'detailed' if performance_analysis['hint_usage_pattern'] == 'frequent' else 'concise'
    }
    
    return content


async def generate_progressive_hints(
    request: HintRequest,
    struggle_analysis: Dict[str, Any],
    db: Session
) -> List[str]:
    """Generate progressive hints for current struggle"""
    
    hints = []
    
    # Level 1: General encouragement and direction
    hints.append(await generate_general_hint(request.context, struggle_analysis))
    
    # Level 2: Specific guidance
    hints.append(await generate_specific_hint(request.context, struggle_analysis))
    
    # Level 3: Step-by-step guidance
    hints.append(await generate_detailed_hint(request.context, struggle_analysis))
    
    # Level 4: Nearly complete solution
    if struggle_analysis.get('difficulty_level') == 'high':
        hints.append(await generate_solution_hint(request.context, struggle_analysis))
    
    return hints


async def analyze_student_struggles(
    session_id: str,
    bubble_id: str,
    context: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Analyze what the student is struggling with"""
    
    # Get recent attempts and errors
    recent_activity = await tracking_service.get_recent_activity(session_id, bubble_id, db)
    
    # Identify common patterns
    struggle_patterns = {
        'repeated_errors': analyze_error_patterns(recent_activity),
        'time_spent': calculate_time_struggle_indicators(recent_activity),
        'hint_requests': count_recent_hint_requests(recent_activity),
        'difficulty_level': assess_difficulty_level(context, recent_activity),
        'specific_concepts': identify_struggling_concepts(context, recent_activity)
    }
    
    return struggle_patterns


def determine_difficulty_level(performance_analysis: Dict[str, Any]) -> str:
    """Determine appropriate difficulty level"""
    
    avg_score = performance_analysis.get('average_score', 0)
    completion_rate = performance_analysis.get('completion_rate', 0)
    
    if avg_score >= 85 and completion_rate >= 0.8:
        return 'advanced'
    elif avg_score >= 70 and completion_rate >= 0.6:
        return 'intermediate'
    else:
        return 'beginner'


def calculate_estimated_time(content: Dict[str, Any], performance_analysis: Dict[str, Any]) -> int:
    """Calculate estimated completion time in minutes"""
    
    base_time = {
        'concept': 15,
        'task': 30,
        'quiz': 20,
        'example': 10,
        'explanation': 8
    }
    
    content_type = content.get('type', 'concept')
    base = base_time.get(content_type, 15)
    
    # Adjust for student pace
    pace_multiplier = {
        'fast': 0.7,
        'medium': 1.0,
        'slow': 1.4
    }
    
    student_pace = performance_analysis.get('learning_pace', 'medium')
    multiplier = pace_multiplier.get(student_pace, 1.0)
    
    return int(base * multiplier)


def extract_learning_objectives(content_type: str) -> List[str]:
    """Extract learning objectives for content type"""
    
    objectives_map = {
        'concept': [
            'Understand core principles',
            'Identify key relationships',
            'Apply knowledge to examples'
        ],
        'task': [
            'Implement solution logic',
            'Debug and test code',
            'Apply best practices'
        ],
        'quiz': [
            'Demonstrate knowledge',
            'Apply concepts accurately',
            'Identify correct solutions'
        ]
    }
    
    return objectives_map.get(content_type, ['Learn and apply new concepts'])


async def track_adaptive_content_generation(
    session_id: str,
    content_type: str,
    content: Dict[str, Any],
    db: Session
):
    """Track adaptive content generation for analytics"""
    
    event_data = {
        'session_id': session_id,
        'content_type': content_type,
        'difficulty_level': content.get('difficulty', 'unknown'),
        'complexity': content.get('complexity', 'unknown')
    }
    
    # Log to analytics
    await tracking_service.log_event(
        session_id=session_id,
        event_type=EventType.ADAPTIVE_CONTENT_GENERATED,
        event_data=event_data,
        db=db
    )


async def track_hint_usage(
    session_id: str,
    bubble_id: str,
    hint_level: int,
    db: Session
):
    """Track hint usage for analytics"""
    
    event_data = {
        'session_id': session_id,
        'bubble_id': bubble_id,
        'hint_level': hint_level
    }
    
    await tracking_service.log_event(
        session_id=session_id,
        event_type=EventType.HINT_REQUESTED,
        event_data=event_data,
        db=db
    )


# Placeholder implementations for AI content generation
# In production, these would call actual AI services

async def generate_concept_text(topic: str, complexity: str) -> str:
    return f"Adaptive concept content for {topic} at {complexity} level..."

async def generate_concept_examples(topic: str, complexity: str) -> List[str]:
    return [f"Example 1 for {topic}", f"Example 2 for {topic}"]

async def extract_key_points(topic: str, complexity: str) -> List[str]:
    return [f"Key point 1 about {topic}", f"Key point 2 about {topic}"]

async def generate_interactive_elements(topic: str, style: str) -> Dict[str, Any]:
    return {"type": style, "elements": []}

async def generate_task_instructions(topic: str, difficulty: str, scaffolding: str) -> str:
    return f"Task instructions for {topic} (difficulty: {difficulty}, scaffolding: {scaffolding})"

async def generate_starter_code(topic: str, scaffolding: str) -> str:
    if scaffolding == 'high':
        return f"// Starter code with high scaffolding for {topic}\n// TODO: Complete the implementation"
    return f"// Starter code for {topic}"

async def generate_test_cases(topic: str, difficulty: str) -> List[Dict[str, Any]]:
    return [{"input": "test", "output": "result", "description": f"Test case for {topic}"}]

async def generate_task_hints(topic: str, performance: Dict[str, Any]) -> List[str]:
    return [f"Hint 1 for {topic}", f"Hint 2 for {topic}"]

async def define_success_criteria(topic: str, difficulty: str) -> Dict[str, Any]:
    return {"criteria": f"Success criteria for {topic} at {difficulty} level"}

async def generate_quiz_questions(topic: str, weak_areas: List[str], performance: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{"question": f"Question about {topic}", "type": "multiple_choice", "options": []}]

async def generate_general_hint(context: Dict[str, Any], struggle: Dict[str, Any]) -> str:
    return "Take a step back and think about the main concept here..."

async def generate_specific_hint(context: Dict[str, Any], struggle: Dict[str, Any]) -> str:
    return "Look at the specific area where you're having trouble..."

async def generate_detailed_hint(context: Dict[str, Any], struggle: Dict[str, Any]) -> str:
    return "Here's a step-by-step approach to solve this..."

async def generate_solution_hint(context: Dict[str, Any], struggle: Dict[str, Any]) -> str:
    return "Here's almost the complete solution..." 