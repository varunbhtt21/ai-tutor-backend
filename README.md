# AI Tutor Backend

Real-time teaching pipeline: **browser mic → WebSocket → Whisper STT → Dialogue/State Manager → LLM responses → Voice TTS**

Complete AI tutor with curriculum-driven conversation and voice interaction capabilities.

## Setup & Installation

### 1. Environment Setup
```bash
# Create and activate virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration:
# - OpenAI API key for GPT-4o and TTS (required)
# - Database URL (optional, defaults to SQLite)
```

**Required Environment Variables:**
```bash
OPENAI_API_KEY=your_openai_api_key_here  # Required for AI features
DATABASE_URL=sqlite:///./ai_tutor.db     # Default SQLite database
```

### 3. Database Setup

#### Initial Migration Setup
```bash
# Apply migrations to database
./migrations.sh upgrade

# Initialize curriculum data
uv run python initialize_curriculum.py
```

#### Migration Workflow
```bash
# Create new migration after model changes
./migrations.sh create "Description of changes"

# Apply pending migrations
./migrations.sh upgrade

# Check current migration version
./migrations.sh current

# View migration history
./migrations.sh history

# Rollback to previous migration
./migrations.sh downgrade

# Rollback to specific migration
./migrations.sh downgrade <revision_id>
```

## Running the Application

### Development Server
```bash
# Using the provided script
./run_backend.sh

# Or manually
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check with database status
- `WS /ws/lesson/{session_id}` - **Main WebSocket endpoint for AI tutoring**

## Features

### ✅ **Phase 0-3: Complete Core System**
- **Audio Input**: WebSocket + Whisper STT for speech recognition
- **Intelligent Conversation**: GPT-4o powered educational dialogue
- **Curriculum Engine**: Learning graph with personalized paths
- **Progress Tracking**: Mastery scoring and concept prerequisites
- **Real-time WebSocket**: Bidirectional communication

### ✅ **Phase 4: Voice Output & TTS** (Current)
- **Text-to-Speech**: OpenAI TTS API integration
- **Voice Selection**: 6 different voices (alloy, echo, fable, onyx, nova, shimmer)
- **Audio Response**: Complete audio conversation loop
- **Voice Settings**: Customizable speed and format
- **Base64 Streaming**: Efficient audio delivery via WebSocket

## Database Models

### Core Models
- **LearningSession**: User sessions with audio preferences
- **ConversationLog**: Interaction history with audio metrics
- **LearningMetrics**: Performance and engagement tracking

### Curriculum Models  
- **LearningConcept**: Core curriculum concepts with content
- **ConceptPrerequisite**: Learning dependencies and sequences
- **StudentProgress**: Individual mastery and confidence tracking
- **LearningPath**: Personalized learning journeys
- **AssessmentResult**: Knowledge check results and recommendations

## Development Workflow

1. **Make model changes** in `app/models/`
2. **Create migration**: `./migrations.sh create "description"`
3. **Apply migration**: `./migrations.sh upgrade`
4. **Test changes** with `/health` endpoint

## Testing

### Phase 4 TTS Testing
```bash
# Test TTS functionality (requires OpenAI API key)
export OPENAI_API_KEY=your_key_here
uv run python test_phase4_tts.py
```

### WebSocket Testing  
```bash
# Use the frontend test suite
cd ../ai-frontend
uv run python test_conversation.py
```

## Architecture

```
app/
├── main.py              # FastAPI application  
├── database.py          # SQLAlchemy setup
├── models/              # Database models
│   ├── session.py       #   Core session models
│   └── learning_graph.py#   Curriculum models
├── services/            # Business logic
│   ├── audio_service.py #   Whisper STT processing
│   ├── tts_service.py   #   OpenAI TTS integration  
│   ├── conversation_service.py  # GPT-4o dialogue
│   └── learning_graph_service.py # Curriculum engine
├── websocket/           # WebSocket handlers
├── conversation/        # Dialogue state management
└── __init__.py

lesson_graphs/           # Curriculum data
├── python_curriculum.py# Structured learning content  
└── __init__.py

alembic/                 # Database migrations
├── versions/            # Generated migration files
└── env.py              # Migration configuration
```