# AI Tutor Backend

Interactive learning platform with bubble graph navigation - Backend API

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- uv (for package management)

### Setup Instructions

1. **Clone and Navigate**
   ```bash
   cd ai-tutor-backend
   ```

2. **Create Virtual Environment with uv**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   uv pip install -e .
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (see Configuration section)
   ```

5. **Database Setup**
   ```bash
   # Install PostgreSQL (macOS)
   brew install postgresql
   brew services start postgresql
   
   # Create database
   createdb ai_tutor_dev
   
   # Run migrations
   alembic upgrade head
   ```

6. **Test Setup**
   ```bash
   python scripts/test_connection.py
   ```

7. **Run Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📁 Project Structure

```
ai-tutor-backend/
├── app/
│   ├── core/           # Core configuration and utilities
│   ├── models/         # Database models (centralized)
│   ├── api/            # API routes
│   ├── services/       # Business logic services
│   └── schemas/        # Pydantic schemas
├── alembic/            # Database migrations
├── tests/              # Test files
├── scripts/            # Utility scripts
└── pyproject.toml      # Project configuration
```

## ⚙️ Configuration

Key environment variables (update in `.env`):

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/ai_tutor_dev

# Security
SECRET_KEY=your-super-secret-key
OPENAI_API_KEY=sk-your-openai-api-key

# Development
DEBUG=true
```

## 🗄️ Database Management

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Sample Data
```bash
# Seed database with sample data
python scripts/seed_data.py
```

## 🧪 Testing

### Run Test Script
```bash
python scripts/test_connection.py
```

### Unit Tests
```bash
pytest tests/
```

## 📊 Development Tools

### Code Formatting
```bash
uv pip install black isort
black app/
isort app/
```

### API Documentation
- FastAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Architecture

### Models
All models are centralized in `app/models/` for architectural consistency:
- `User` - Authentication and user management
- `Course` - Learning content organization
- `Session` - Bubble graph sessions
- `BubbleNode` - Individual learning bubbles
- `StudentState` - Progress tracking
- `EventLog` & `CoinTransaction` - Analytics and gamification

### Services
- **Tutor Orchestrator** - AI conversation management
- **AI Service** - OpenAI integration
- **Grader Service** - Code execution and evaluation
- **Gamification** - Coins and achievements

## 🔧 Development Workflow

1. **Make Changes** to models/api/services
2. **Create Migration** if models changed
3. **Test Changes** with test scripts
4. **Run Tests** to ensure stability
5. **Fix Issues** following RCA approach

## 🐛 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql

# Create database if missing
createdb ai_tutor_dev
```

**Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv pip install -e .
```

**Migration Issues**
```bash
# Reset migrations (development only)
alembic downgrade base
alembic upgrade head
```

## 📝 API Endpoints

### Health Check
- `GET /` - Basic info
- `GET /health` - System health

### Authentication (Coming Soon)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`

### Courses (Coming Soon)
- `GET /api/v1/courses/`
- `POST /api/v1/courses/`

### Sessions (Coming Soon)
- `GET /api/v1/sessions/`
- `POST /api/v1/sessions/`

## 🎯 Next Phase Implementation

Phase 2 will add:
- Bubble graph builder API
- Session management
- Graph traversal logic
- Basic authentication

---

Built with ❤️ for interactive learning