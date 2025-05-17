from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os

# Create SQLAlchemy instance
db = SQLAlchemy()

# Create database engine with absolute path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emerald_altar.db')
engine = create_engine(f'sqlite:///{db_path}')

# Create session factory
session_factory = sessionmaker(bind=engine)

# Create thread-safe scoped session
Session = scoped_session(session_factory)

def init_db():
    db.create_all()
