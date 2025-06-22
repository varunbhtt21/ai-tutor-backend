#!/usr/bin/env python3
"""
Test script for the ask_gpt function
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.ai_utils import ask_gpt, is_ai_available

def main():
    """Test the ask_gpt function"""
    
    print("🤖 Testing AI Integration")
    print("=" * 50)
    
    # Check if AI is available
    if not is_ai_available():
        print("❌ AI service is not available. Please check your OpenAI API key in .env")
        return
    
    print("✅ AI service is available!")
    print()
    
    # Test 1: Simple question
    print("Test 1: Simple question")
    print("-" * 30)
    response = ask_gpt("What is a tomato?")
    print(f"Question: What is a tomato?")
    print(f"Answer: {response}")
    print()
    
    # Test 2: Educational question with custom system prompt
    print("Test 2: Educational question with tutor context")
    print("-" * 50)
    tutor_prompt = """You are an expert programming tutor. Explain concepts clearly and provide examples. 
    Keep explanations beginner-friendly but accurate."""
    
    response = ask_gpt(
        "What is a variable in programming?", 
        system_prompt=tutor_prompt
    )
    print(f"Question: What is a variable in programming?")
    print(f"Answer: {response}")
    print()
    
    # Test 3: Code explanation
    print("Test 3: Code explanation")
    print("-" * 30)
    code_question = """
    Explain this Python code:
    
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n-1)
    """
    
    response = ask_gpt(code_question, system_prompt=tutor_prompt)
    print(f"Question: {code_question.strip()}")
    print(f"Answer: {response}")
    print()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main() 