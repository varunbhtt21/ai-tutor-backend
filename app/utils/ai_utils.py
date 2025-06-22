"""
AI Utility Functions
Simple utilities for interacting with OpenAI API
"""

import logging
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize the OpenAI client globally
try:
    if hasattr(settings, 'openai_api_key') and settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
        client = OpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI client initialized successfully")
    else:
        client = None
        logger.warning("OpenAI API key not configured - AI features will be disabled")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None


def ask_gpt(question: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """
    Simple utility function to ask GPT a question
    
    Args:
        question: The question to ask
        system_prompt: Optional system prompt to set context
        
    Returns:
        The AI response as a string
    
    Example:
        response = ask_gpt("What is a tomato?")
        print(response)
    """
    if not client:
        return "AI service is currently unavailable. Please try again later."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


def is_ai_available() -> bool:
    """Check if AI service is available"""
    return client is not None


# Example usage (can be run as a script)
if __name__ == "__main__":
    # Test the ask_gpt function
    response = ask_gpt("What is a tomato?")
    print(response) 