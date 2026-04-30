import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.models import Base

@st.cache_resource
def get_engine():
    return create_engine(
        st.secrets["database_url"],
        pool_size=3,
        max_overflow=2,       # Max 5 total — enough for Streamlit
        pool_recycle=300,
        pool_pre_ping=True,
        pool_timeout=30,      # Don't wait forever for a connection
    )

@st.cache_resource
def get_session_factory():
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, expire_on_commit=False)

# Use this everywhere — never call Session() directly
from contextlib import contextmanager

@contextmanager
def get_db():
    Session = get_session_factory()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables():
    """Run once to create tables from your models."""
    Base.metadata.create_all(get_engine())