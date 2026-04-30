import streamlit as st
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker

from models.models import Base
from contextlib import contextmanager
def get_engine():
    """No caching — NullPool means each call is a fresh connection."""
    return create_engine(
        st.secrets["database_url"],
        poolclass=NullPool,  # ← connection closed immediately after use
    )

@contextmanager
def get_db():
    engine = get_engine()
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def create_tables():
    """Run once to create tables from your models."""
    Base.metadata.create_all(get_engine())