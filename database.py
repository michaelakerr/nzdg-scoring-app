import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from models.models import Base
from contextlib import contextmanager

@st.cache_resource
def get_engine():
    """Cached once per app lifetime — reuses the connection pool."""
    return create_engine(
        st.secrets["database_url"],
        poolclass=QueuePool,
        pool_size=5,          # number of connections to keep open
        max_overflow=1,      # extra connections allowed beyond pool_size
        pool_timeout=30,      # seconds to wait for a connection before error
        pool_pre_ping=True,   # verify connections are alive before using them
        pool_recycle=300,    # recycle connections after 5 min (avoids stale connections)
    )

@contextmanager
def get_db():
    Session = sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=True,
    )
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()   # returns the connection back to the pool


def create_tables():
    """Run once to create tables from your models."""
    Base.metadata.create_all(get_engine())