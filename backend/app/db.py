from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os
from contextlib import contextmanager

# Create SQLAlchemy instance
db = SQLAlchemy()

# Create database engine with absolute path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emerald_altar.db')
engine = create_engine(f'sqlite:///{db_path}', pool_size=10, max_overflow=20, pool_timeout=60)

# Create session factory
session_factory = sessionmaker(bind=engine)

# Create thread-safe scoped session
Session = scoped_session(session_factory)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    db.create_all()
