#!/usr/bin/env python3
"""
Test script to validate database connection and basic setup
This script follows the RCA approach: test, identify issues, fix, retest
"""

import sys
import os
import asyncio
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from app.core.config import settings
    from app.core.database import test_connection, engine
    from app.models import User, Course, Session, BubbleNode
    from sqlmodel import Session as DBSession, select
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_config():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        print(f"App Name: {settings.app_name}")
        print(f"Database URL: {settings.database_url}")
        print(f"Debug Mode: {settings.debug}")
        
        # Test required settings
        required_settings = ['secret_key', 'openai_api_key']
        missing = []
        
        for setting in required_settings:
            try:
                value = getattr(settings, setting)
                if not value or value.startswith('your-') or value.startswith('sk-your'):
                    missing.append(setting)
            except AttributeError:
                missing.append(setting)
        
        if missing:
            print(f"⚠️  Missing or placeholder settings: {missing}")
            print("Please update your .env file with actual values")
        else:
            print("✅ Configuration valid")
            
        return len(missing) == 0
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    
    try:
        if test_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            print("Troubleshooting:")
            print("1. Check if PostgreSQL is running")
            print("2. Verify database credentials in .env file")
            print("3. Ensure database exists")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("Troubleshooting:")
        print("1. Install PostgreSQL: brew install postgresql")
        print("2. Start PostgreSQL: brew services start postgresql")
        print("3. Create database: createdb ai_tutor_dev")
        return False


def test_models():
    """Test model imports and basic functionality"""
    print("\n📊 Testing models...")
    
    try:
        # Test model creation (without saving to DB)
        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password="dummy_hash"
        )
        
        course = Course(
            name="Test Course",
            description="A test course",
            instructor_id=1
        )
        
        print("✅ Models can be instantiated")
        print(f"User: {user}")
        print(f"Course: {course}")
        return True
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False


def test_database_operations():
    """Test basic database operations"""
    print("\n💾 Testing database operations...")
    
    if not test_connection():
        print("❌ Skipping database operations - no connection")
        return False
    
    try:
        with DBSession(engine) as session:
            # Test simple query
            result = session.exec(select(User).limit(1))
            users = result.all()
            print(f"✅ Query executed successfully. Found {len(users)} users")
            return True
            
    except Exception as e:
        print(f"❌ Database operations error: {e}")
        print("This might be normal if tables don't exist yet")
        print("Run migrations: alembic upgrade head")
        return False


def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 AI Tutor Backend - Comprehensive Test")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config),
        ("Database Connection", test_database_connection),
        ("Models", test_models),
        ("Database Operations", test_database_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Unexpected error in {name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for troubleshooting.")
        
        if passed == 0:
            print("\n🔧 Quick Setup Guide:")
            print("1. Create .env file: cp .env.example .env")
            print("2. Update .env with your settings")
            print("3. Install PostgreSQL and create database")
            print("4. Run: python scripts/test_connection.py")
    
    return passed == total


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 