import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from utils.config import DATABASE_URL

# Engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Enable SQL logging same as mam's code
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 
Base = declarative_base()


# Init DB — enables pgvector and creates all tables 
def init_db():
    from db import models  
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)