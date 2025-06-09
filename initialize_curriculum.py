#!/usr/bin/env python3
"""
Initialize Python Curriculum for Phase 3 Testing
Populates the database with learning concepts and creates a test learning path
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.curriculum_initializer import initialize_python_curriculum
from app.services.learning_graph_service import LearningGraphService

async def main():
    """Initialize curriculum and set up test data"""
    print("🚀 Initializing Python Curriculum for Phase 3")
    print("=" * 50)
    
    # Initialize curriculum
    print("📚 Setting up learning concepts and prerequisites...")
    result = await initialize_python_curriculum(force_refresh=True)
    
    if result["status"] == "success":
        print(f"✅ Created {result['concepts_created']} concepts")
        print(f"✅ Created {result['prerequisites_created']} prerequisite relationships")
        print("\n📋 Concept Map:")
        for slug, concept_id in result["concept_map"].items():
            print(f"  {slug} -> ID {concept_id}")
    else:
        print(f"❌ Failed to initialize curriculum: {result.get('message', 'Unknown error')}")
        return
    
    # Create a test learning path
    print("\n🛤️  Creating test learning path...")
    learning_graph = LearningGraphService()
    
    try:
        path_result = await learning_graph.create_personalized_path(
            session_id="test_session_phase3",
            user_id="test_user",
            goal="Learn Python fundamentals",
            difficulty_preference=0.5,
            topics=["python-basics", "data-structures", "control-flow"]
        )
        
        print(f"✅ Created learning path: {path_result['name']}")
        print(f"📊 Path contains {path_result['concept_count']} concepts")
        print(f"⏱️  Estimated completion: {path_result['estimated_hours']:.1f} hours")
        
        # Get curriculum summary
        print("\n📈 Curriculum Summary:")
        summary = await learning_graph.get_curriculum_summary()
        
        if "error" not in summary:
            print(f"Total concepts: {summary['concepts_count']}")
            print(f"Total prerequisites: {summary['prerequisites_count']}")
            
            print("\n📚 Available Concepts:")
            for concept in summary["concepts"]:
                print(f"  • {concept['name']} ({concept['category']}) - Level {concept['difficulty']}")
            
            print("\n🔗 Prerequisites:")
            for prereq in summary["prerequisites"]:
                print(f"  • {prereq['prerequisite']} → {prereq['concept']} ({prereq['type']})")
        
        # Validate integrity
        print("\n🔍 Validating curriculum integrity...")
        validation = await learning_graph.validate_curriculum_integrity()
        
        if validation["is_valid"]:
            print("✅ Curriculum integrity check passed!")
        else:
            print(f"⚠️  Found {validation['total_issues']} issues:")
            for issue in validation["issues"]:
                print(f"  • {issue}")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
    
    finally:
        learning_graph.close()
    
    print("\n🎉 Phase 3 curriculum initialization complete!")
    print("You can now test the curriculum-driven conversation system.")

if __name__ == "__main__":
    asyncio.run(main()) 