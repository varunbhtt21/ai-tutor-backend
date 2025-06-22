# AI Integration Guide

This guide shows how to use the `ask_gpt` function throughout the AI Tutor application.

## Quick Start

The simplest way to use AI in your code is with the `ask_gpt` utility function:

```python
from app.utils.ai_utils import ask_gpt

# Simple usage
response = ask_gpt("What is a tomato?")
print(response)
```

## Configuration

Make sure you have your OpenAI API key configured in your `.env` file:

```env
OPENAI_API_KEY=your-actual-openai-api-key-here
```

## Usage Examples

### 1. Basic Question

```python
from app.utils.ai_utils import ask_gpt

response = ask_gpt("What is a tomato?")
print(response)
```

### 2. Educational Context

```python
from app.utils.ai_utils import ask_gpt

# Use a custom system prompt for educational context
tutor_prompt = """You are an expert programming tutor. 
Explain concepts clearly with examples. Keep explanations beginner-friendly."""

response = ask_gpt(
    "What is a variable in programming?", 
    system_prompt=tutor_prompt
)
print(response)
```

### 3. Code Review

```python
from app.utils.ai_utils import ask_gpt

code_to_review = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
"""

review_prompt = """You are a code reviewer. Analyze the code and provide feedback on:
1. Correctness
2. Efficiency  
3. Best practices
4. Potential improvements"""

response = ask_gpt(
    f"Please review this Python code:\n\n{code_to_review}",
    system_prompt=review_prompt
)
print(response)
```

### 4. In API Endpoints

```python
from fastapi import APIRouter
from app.utils.ai_utils import ask_gpt, is_ai_available

router = APIRouter()

@router.post("/ai-help")
async def get_ai_help(question: str):
    if not is_ai_available():
        return {"error": "AI service is currently unavailable"}
    
    response = ask_gpt(
        question,
        system_prompt="You are a helpful educational assistant."
    )
    
    return {"response": response}
```

### 5. In Services

```python
from app.utils.ai_utils import ask_gpt

class TutoringService:
    def get_explanation(self, concept: str, student_level: str):
        prompt = f"""You are teaching a {student_level} level student. 
        Explain concepts at an appropriate level with relevant examples."""
        
        response = ask_gpt(
            f"Explain {concept}",
            system_prompt=prompt
        )
        
        return response
```

## Advanced Usage

### Error Handling

```python
from app.utils.ai_utils import ask_gpt, is_ai_available

def safe_ai_call(question: str):
    try:
        if not is_ai_available():
            return "AI service is currently unavailable"
        
        response = ask_gpt(question)
        return response
        
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return "Sorry, I encountered an error while processing your request"
```

### Custom System Prompts for Different Contexts

```python
# For programming help
PROGRAMMING_TUTOR = """You are an expert programming instructor. 
Provide clear, accurate explanations with code examples. 
Encourage best practices and help students understand concepts deeply."""

# For math help  
MATH_TUTOR = """You are a patient mathematics tutor.
Break down complex problems into steps.
Use analogies and visual descriptions when helpful."""

# For general learning
LEARNING_ASSISTANT = """You are a supportive learning assistant.
Adapt your explanations to the student's level.
Encourage curiosity and provide additional resources when relevant."""

# Usage
response = ask_gpt("How do loops work?", system_prompt=PROGRAMMING_TUTOR)
```

## API Endpoints

### Simple AI Question Endpoint

```
POST /api/v1/ai-tutor/ask-simple
```

Request body:
```json
{
    "question": "What is a tomato?",
    "system_prompt": "You are a helpful assistant."
}
```

Response:
```json
{
    "response": "A tomato is a fruit that is botanically classified as a berry...",
    "ai_available": true
}
```

### AI Status Check

```
GET /api/v1/ai-tutor/status
```

Response:
```json
{
    "ai_available": true,
    "model": "gpt-4o-mini",
    "features": {
        "personalized_responses": true,
        "contextual_hints": true,
        "code_feedback": true,
        "learning_paths": true,
        "adaptive_questions": true,
        "simple_ask_gpt": true
    }
}
```

## Testing

Run the test script to verify AI integration:

```bash
cd ai-tutor-backend
python scripts/test_ask_gpt.py
```

## Best Practices

1. **Always check availability**: Use `is_ai_available()` before making AI calls
2. **Handle errors gracefully**: Wrap AI calls in try-catch blocks
3. **Use appropriate system prompts**: Tailor the context to your specific use case
4. **Keep questions focused**: More specific questions get better responses
5. **Log AI interactions**: For debugging and analytics

## Configuration Details

The `ask_gpt` function uses:
- **Model**: `gpt-4o-mini` (cost-effective and fast)
- **API Key**: Loaded from `OPENAI_API_KEY` environment variable
- **Error Handling**: Built-in error handling with fallback messages

## Integration with Existing AI Tutor Service

The existing `AITutorService` has been updated to use the `ask_gpt` function internally, so all existing AI tutoring features continue to work while now using the simplified API pattern you requested.

## Troubleshooting

1. **"AI service is currently unavailable"**: Check your OpenAI API key in `.env`
2. **Import errors**: Make sure you're importing from `app.utils.ai_utils`
3. **API key issues**: Verify the key is correctly set and has sufficient credits

## Example: Complete Integration

Here's a complete example showing how to integrate the `ask_gpt` function in a new feature:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.ai_utils import ask_gpt, is_ai_available

router = APIRouter()

class StudyHelperRequest(BaseModel):
    topic: str
    difficulty_level: str
    question_type: str  # "explanation", "example", "practice"

@router.post("/study-helper")
async def get_study_help(request: StudyHelperRequest):
    if not is_ai_available():
        raise HTTPException(status_code=503, detail="AI service unavailable")
    
    # Create context-specific system prompt
    prompts = {
        "explanation": f"You are teaching a {request.difficulty_level} student. Provide a clear explanation.",
        "example": f"You are providing examples for a {request.difficulty_level} student. Give practical examples.",
        "practice": f"You are creating practice problems for a {request.difficulty_level} student. Make it engaging."
    }
    
    system_prompt = prompts.get(request.question_type, prompts["explanation"])
    
    # Generate question based on type
    questions = {
        "explanation": f"Explain {request.topic}",
        "example": f"Give me practical examples of {request.topic}",
        "practice": f"Create a practice problem about {request.topic}"
    }
    
    question = questions.get(request.question_type, questions["explanation"])
    
    try:
        response = ask_gpt(question, system_prompt=system_prompt)
        return {
            "topic": request.topic,
            "difficulty_level": request.difficulty_level,
            "question_type": request.question_type,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")
```

This integration guide should help you use the `ask_gpt` function effectively throughout your application! 🚀 