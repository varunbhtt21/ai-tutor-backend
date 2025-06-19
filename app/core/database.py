"""
Database connection and session management
"""

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)


def create_db_and_tables():
    """Create database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()


# Alias for FastAPI dependency injection
def get_db() -> Generator[Session, None, None]:
    """Get database session for FastAPI dependency injection"""
    return get_session()


# Test database connection
def test_connection():
    """Test database connection"""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False 