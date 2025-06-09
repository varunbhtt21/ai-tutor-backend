"""
Curriculum Initializer Service
Populates the database with learning concepts and prerequisites
"""

import asyncio
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal
from app.models.learning_graph import (
    LearningConcept, ConceptPrerequisite, DifficultyLevel, PrerequisiteType
)
from lesson_graphs.python_curriculum import get_curriculum_data

class CurriculumInitializer:
    """Service for initializing curriculum data in database"""
    
    def __init__(self):
        self.db_session = None
    
    def get_db(self) -> Session:
        """Get database session"""
        if not self.db_session:
            self.db_session = SessionLocal()
        return self.db_session
    
    async def initialize_curriculum(self, force_refresh: bool = False) -> Dict:
        """Initialize curriculum data in database"""
        db = self.get_db()
        
        try:
            # Check if curriculum already exists
            existing_concepts = db.query(LearningConcept).count()
            
            if existing_concepts > 0 and not force_refresh:
                return {
                    "status": "already_initialized",
                    "message": f"Found {existing_concepts} existing concepts. Use force_refresh=True to reinitialize.",
                    "concepts_count": existing_concepts
                }
            
            if force_refresh:
                # Clear existing data
                await self._clear_existing_data()
            
            # Load curriculum data
            curriculum_data = get_curriculum_data()
            
            # Create concepts
            concept_map = await self._create_concepts(curriculum_data["concepts"])
            
            # Create prerequisites
            prereq_count = await self._create_prerequisites(
                curriculum_data["prerequisites"], 
                concept_map
            )
            
            db.commit()
            
            return {
                "status": "success",
                "message": "Curriculum initialized successfully",
                "concepts_created": len(concept_map),
                "prerequisites_created": prereq_count,
                "concept_map": {slug: concept_id for slug, concept_id in concept_map.items()}
            }
            
        except Exception as e:
            db.rollback()
            return {
                "status": "error",
                "message": f"Failed to initialize curriculum: {str(e)}"
            }
        finally:
            db.close()
    
    async def _clear_existing_data(self):
        """Clear existing curriculum data"""
        db = self.get_db()
        
        # Delete in order to respect foreign key constraints
        db.query(ConceptPrerequisite).delete()
        db.query(LearningConcept).delete()
        
        print("Cleared existing curriculum data")
    
    async def _create_concepts(self, concepts_data: List[Dict]) -> Dict[str, int]:
        """Create learning concepts in database"""
        db = self.get_db()
        concept_map = {}  # slug -> concept_id mapping
        
        for concept_data in concepts_data:
            concept = LearningConcept(
                name=concept_data["name"],
                slug=concept_data["slug"],
                description=concept_data["description"],
                learning_objectives=concept_data["learning_objectives"],
                difficulty_level=concept_data["difficulty_level"],
                estimated_time_minutes=concept_data["estimated_time_minutes"],
                category=concept_data["category"],
                explanation_text=concept_data["explanation_text"],
                code_examples=concept_data["code_examples"],
                practice_exercises=concept_data["practice_exercises"],
                assessment_questions=concept_data["assessment_questions"],
                mastery_threshold=concept_data["mastery_threshold"]
            )
            
            db.add(concept)
            db.flush()  # Get the ID without committing
            
            concept_map[concept.slug] = concept.id
            print(f"Created concept: {concept.name} (ID: {concept.id})")
        
        return concept_map
    
    async def _create_prerequisites(
        self, 
        prerequisites_data: List[Dict], 
        concept_map: Dict[str, int]
    ) -> int:
        """Create prerequisite relationships"""
        db = self.get_db()
        created_count = 0
        
        for prereq_data in prerequisites_data:
            concept_slug = prereq_data["concept"]
            prerequisite_slug = prereq_data["prerequisite"]
            
            if concept_slug not in concept_map:
                print(f"Warning: Concept '{concept_slug}' not found in concept_map")
                continue
                
            if prerequisite_slug not in concept_map:
                print(f"Warning: Prerequisite '{prerequisite_slug}' not found in concept_map")
                continue
            
            concept_id = concept_map[concept_slug]
            prerequisite_id = concept_map[prerequisite_slug]
            
            # Check if prerequisite relationship already exists
            existing = db.query(ConceptPrerequisite).filter(
                and_(
                    ConceptPrerequisite.concept_id == concept_id,
                    ConceptPrerequisite.prerequisite_id == prerequisite_id
                )
            ).first()
            
            if existing:
                print(f"Prerequisite relationship already exists: {prerequisite_slug} -> {concept_slug}")
                continue
            
            prerequisite = ConceptPrerequisite(
                concept_id=concept_id,
                prerequisite_id=prerequisite_id,
                prerequisite_type=prereq_data["type"],
                strength=prereq_data["strength"]
            )
            
            db.add(prerequisite)
            created_count += 1
            
            print(f"Created prerequisite: {prerequisite_slug} -> {concept_slug} ({prereq_data['type']})")
        
        return created_count
    
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
        finally:
            db.close()
    
    async def validate_curriculum_integrity(self) -> Dict:
        """Validate curriculum data integrity"""
        db = self.get_db()
        issues = []
        
        try:
            # Check for orphaned prerequisites
            prerequisites = db.query(ConceptPrerequisite).all()
            for prereq in prerequisites:
                concept = db.query(LearningConcept).filter(
                    LearningConcept.id == prereq.concept_id
                ).first()
                prerequisite_concept = db.query(LearningConcept).filter(
                    LearningConcept.id == prereq.prerequisite_id
                ).first()
                
                if not concept:
                    issues.append(f"Orphaned prerequisite: concept_id {prereq.concept_id} not found")
                
                if not prerequisite_concept:
                    issues.append(f"Orphaned prerequisite: prerequisite_id {prereq.prerequisite_id} not found")
            
            # Check for circular dependencies (simplified check)
            concepts = db.query(LearningConcept).all()
            for concept in concepts:
                if await self._has_circular_dependency(concept.id, set(), db):
                    issues.append(f"Circular dependency detected involving concept: {concept.name}")
            
            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "total_issues": len(issues)
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Validation failed: {str(e)}"
            }
        finally:
            db.close()
    
    async def _has_circular_dependency(
        self, 
        concept_id: int, 
        visited: set, 
        db: Session,
        max_depth: int = 10
    ) -> bool:
        """Check for circular dependencies (simplified implementation)"""
        if max_depth <= 0:
            return False  # Prevent infinite recursion
            
        if concept_id in visited:
            return True  # Circular dependency found
        
        visited.add(concept_id)
        
        # Get prerequisites of this concept
        prerequisites = db.query(ConceptPrerequisite).filter(
            ConceptPrerequisite.concept_id == concept_id
        ).all()
        
        for prereq in prerequisites:
            if await self._has_circular_dependency(
                prereq.prerequisite_id, 
                visited.copy(), 
                db, 
                max_depth - 1
            ):
                return True
        
        return False
    
    def close(self):
        """Close database session"""
        if self.db_session:
            self.db_session.close()
            self.db_session = None

# Convenience function for easy initialization
async def initialize_python_curriculum(force_refresh: bool = False) -> Dict:
    """Initialize Python curriculum in database"""
    initializer = CurriculumInitializer()
    try:
        result = await initializer.initialize_curriculum(force_refresh)
        return result
    finally:
        initializer.close() 