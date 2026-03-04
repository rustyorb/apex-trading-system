"""
Database Models and Connection

SQLAlchemy ORM models for database interactions.
"""

import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    """
    Database connection manager.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string
        """
        try:
            self.engine = create_engine(
                database_url,
                poolclass=NullPool,  # No connection pooling for simplicity
                echo=False
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("✅ Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_session(self):
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    async def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("🔌 Database connection closed")
