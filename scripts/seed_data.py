#!/usr/bin/env python3
"""
Seed script to populate database with sample data for testing
"""

import sys
import os
from datetime import datetime
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import engine
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Course, Session, BubbleNode, StudentState,
    BubbleType, SessionStatus
)
from sqlmodel import Session as DBSession


def create_sample_users() -> List[User]:
    """Create sample users"""
    users = [
        User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            first_name="Admin",
            last_name="User",
            is_verified=True
        ),
        User(
            username="instructor_john",
            email="john@example.com",
            hashed_password=get_password_hash("instructor123"),
            role=UserRole.INSTRUCTOR,
            first_name="John",
            last_name="Smith",
            is_verified=True
        ),
        User(
            username="student_alice",
            email="alice@example.com",
            hashed_password=get_password_hash("student123"),
            role=UserRole.STUDENT,
            first_name="Alice",
            last_name="Johnson",
            is_verified=True
        ),
        User(
            username="student_bob",
            email="bob@example.com",
            hashed_password=get_password_hash("student123"),
            role=UserRole.STUDENT,
            first_name="Bob",
            last_name="Wilson",
            is_verified=True
        )
    ]
    return users


def create_sample_course(instructor_id: int) -> Course:
    """Create a sample guitar course"""
    return Course(
        name="Guitar Chords 101",
        description="Learn basic guitar chords through interactive lessons",
        subject="Music",
        difficulty_level="beginner",
        estimated_duration=120,
        is_active=True,
        is_public=True,
        learning_objectives=[
            "Master basic major and minor chords",
            "Understand chord progressions", 
            "Play simple songs"
        ],
        tags={"instrument": "guitar", "style": "acoustic"},
        instructor_id=instructor_id
    )


def create_sample_session(course_id: int) -> Session:
    """Create a sample session with bubble graph"""
    graph_json = {
        "start_node": "welcome",
        "nodes": [
            {
                "id": "welcome",
                "type": "concept",
                "title": "Welcome to Guitar Chords",
                "x": 100,
                "y": 100
            },
            {
                "id": "c_major",
                "type": "task", 
                "title": "C Major Chord",
                "x": 300,
                "y": 100
            },
            {
                "id": "g_major",
                "type": "task",
                "title": "G Major Chord", 
                "x": 500,
                "y": 100
            },
            {
                "id": "chord_progression",
                "type": "quiz",
                "title": "Play C-G Progression",
                "x": 400,
                "y": 250
            },
            {
                "id": "summary",
                "type": "summary",
                "title": "Session Summary",
                "x": 400,
                "y": 400
            }
        ],
        "edges": [
            {"from": "welcome", "to": "c_major"},
            {"from": "c_major", "to": "g_major"},
            {"from": "c_major", "to": "chord_progression"},
            {"from": "g_major", "to": "chord_progression"},
            {"from": "chord_progression", "to": "summary"}
        ]
    }
    
    return Session(
        name="Basic Major Chords",
        description="Learn C Major and G Major chords",
        course_id=course_id,
        status=SessionStatus.PUBLISHED,
        graph_json=graph_json,
        max_attempts_per_bubble=3,
        coins_per_bubble=10
    )


def create_sample_bubble_nodes(session_id: int) -> List[BubbleNode]:
    """Create detailed bubble nodes for the session"""
    nodes = [
        BubbleNode(
            node_id="welcome",
            session_id=session_id,
            type=BubbleType.CONCEPT,
            title="Welcome to Guitar Chords",
            content_md="""# Welcome to Guitar Chords 101!

In this lesson, you'll learn your first guitar chords. We'll start with two of the most important chords:

- **C Major** - A bright, happy sound
- **G Major** - Another essential major chord

Let's begin your guitar journey!""",
            tutor_prompt="Welcome the student enthusiastically and explain what they'll learn.",
            success_message="Great! Let's move on to your first chord.",
            coin_reward=5
        ),
        BubbleNode(
            node_id="c_major", 
            session_id=session_id,
            type=BubbleType.TASK,
            title="C Major Chord",
            content_md="""# C Major Chord

The C Major chord is one of the first chords every guitarist learns.

## Finger Placement:
- **1st finger**: 1st fret, B string (2nd string)
- **2nd finger**: 2nd fret, D string (4th string)  
- **3rd finger**: 3rd fret, A string (5th string)

## Strum all strings except the low E string.

Practice this chord until it sounds clear!""",
            hints=[
                "Keep your thumb behind the neck",
                "Press firmly but don't overdo it",
                "Make sure each string rings clearly"
            ],
            tutor_prompt="Help the student learn proper finger placement for C Major chord.",
            success_message="Excellent! Your C Major chord sounds great!",
            failure_message="Keep practicing - finger placement takes time to master.",
            coin_reward=15
        ),
        BubbleNode(
            node_id="g_major",
            session_id=session_id,
            type=BubbleType.TASK,
            title="G Major Chord",
            content_md="""# G Major Chord

The G Major chord has a rich, full sound and uses more strings than C Major.

## Finger Placement:
- **2nd finger**: 3rd fret, low E string (6th string)
- **1st finger**: 2nd fret, A string (5th string)
- **3rd finger**: 3rd fret, B string (2nd string)
- **4th finger**: 3rd fret, high E string (1st string)

## Strum all six strings!

This chord might feel harder at first - that's normal!""",
            hints=[
                "Use your fingertips, not the pads",
                "Arch your fingers to avoid touching other strings",
                "Practice switching between C and G slowly"
            ],
            tutor_prompt="Guide the student through G Major chord formation.",
            success_message="Fantastic! G Major is sounding good!",
            failure_message="G Major is tricky at first. Keep practicing!",
            coin_reward=15
        ),
        BubbleNode(
            node_id="chord_progression",
            session_id=session_id,
            type=BubbleType.QUIZ,
            title="Play C-G Progression",
            content_md="""# Chord Progression Challenge

Now let's put both chords together! 

## Your Task:
Play this progression slowly:
**C Major (4 strums) → G Major (4 strums) → C Major (4 strums) → G Major (4 strums)**

## Tips:
- Count: "1, 2, 3, 4" for each chord
- Switch chords on beat 1
- Don't worry about speed - focus on clean chord changes

This is the foundation of thousands of songs!""",
            hints=[
                "Practice the chord change without strumming first",
                "Keep a steady rhythm",
                "It's okay to pause briefly between chords while learning"
            ],
            tutor_prompt="Evaluate the student's chord progression and provide encouraging feedback.",
            success_message="Amazing! You just played your first chord progression!",
            failure_message="Good attempt! Chord changes take practice - try again.",
            coin_reward=25
        ),
        BubbleNode(
            node_id="summary",
            session_id=session_id,
            type=BubbleType.SUMMARY,
            title="Session Summary",
            content_md="""# Congratulations! 🎉

You've completed your first guitar lesson! Here's what you accomplished:

## ✅ Skills Learned:
- **C Major chord** - Clean finger placement
- **G Major chord** - Using all four fingers
- **Chord progression** - C-G-C-G pattern

## 🎯 Next Steps:
- Practice these chords daily for 5-10 minutes
- Try playing along with simple songs
- Work on smooth chord transitions

## 🏆 Your Progress:
You've earned coins and built the foundation for guitar playing!

Keep practicing - you're on your way to becoming a guitarist! 🎸""",
            tutor_prompt="Celebrate the student's progress and motivate them for continued learning.",
            success_message="You're officially a guitarist now! Keep practicing!",
            coin_reward=20
        )
    ]
    return nodes


def seed_database():
    """Seed the database with sample data"""
    print("🌱 Seeding database with sample data...")
    
    try:
        with DBSession(engine) as session:
            # Create users
            print("👥 Creating users...")
            users = create_sample_users()
            for user in users:
                session.add(user)
            session.commit()
            
            # Refresh to get IDs
            for user in users:
                session.refresh(user)
            
            instructor = next(u for u in users if u.role == UserRole.INSTRUCTOR)
            students = [u for u in users if u.role == UserRole.STUDENT]
            
            # Create course
            print("📚 Creating course...")
            course = create_sample_course(instructor.id)
            session.add(course)
            session.commit()
            session.refresh(course)
            
            # Create session
            print("🎯 Creating session...")
            learning_session = create_sample_session(course.id)
            session.add(learning_session)
            session.commit()
            session.refresh(learning_session)
            
            # Create bubble nodes
            print("🔵 Creating bubble nodes...")
            bubble_nodes = create_sample_bubble_nodes(learning_session.id)
            for node in bubble_nodes:
                session.add(node)
            session.commit()
            
            # Create student states
            print("📊 Creating student states...")
            for student in students:
                student_state = StudentState(
                    student_id=student.id,
                    session_id=learning_session.id,
                    current_node_id="welcome",
                    completed_nodes=[],
                    total_coins=0
                )
                session.add(student_state)
            
            session.commit()
            
            print("✅ Database seeded successfully!")
            print(f"Created {len(users)} users, 1 course, 1 session, {len(bubble_nodes)} bubble nodes")
            print("\nSample credentials:")
            print("Admin: admin / admin123")
            print("Instructor: instructor_john / instructor123") 
            print("Student: student_alice / student123")
            print("Student: student_bob / student123")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise


if __name__ == "__main__":
    seed_database() 