# AI Tutor Backend

Real-time teaching pipeline with WebSocket support for interactive learning.

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

# Edit .env with your database credentials
# DATABASE_URL=postgresql://username:password@localhost:5432/ai_tutor_db
```

### 3. Database Setup

#### Initial Migration Setup
```bash
# Create initial migration
./migrations.sh init

# Apply migrations to database
./migrations.sh upgrade
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
- `WS /ws/lesson/{session_id}` - WebSocket for lessons (coming in Phase 1)

## Database Models

### LearningSession
Tracks user learning sessions and their status.

### ConversationLog  
Logs all conversation interactions with metrics.

### LearningMetrics
Stores learning progress and performance metrics.

## Development Workflow

1. **Make model changes** in `app/models/`
2. **Create migration**: `./migrations.sh create "description"`
3. **Apply migration**: `./migrations.sh upgrade`
4. **Test changes** with `/health` endpoint

## Architecture

```
app/
├── main.py              # FastAPI application
├── database/
│   ├── config.py        # SQLAlchemy setup
│   └── __init__.py
├── models/
│   ├── session.py       # Database models
│   └── __init__.py
├── websocket/           # WebSocket handlers (Phase 1)
└── conversation/        # Dialogue manager (Phase 2)

alembic/                 # Migration files
├── versions/            # Generated migrations
├── env.py              # Alembic configuration
└── script.py.mako      # Migration template
```