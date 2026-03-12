import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.models import Base

@st.cache_resource
def get_engine():
    engine = create_engine(
        st.secrets["database_url"],
        pool_pre_ping=True,       # handles Neon's connection sleep
        pool_size=5,
        max_overflow=10,
    )
    return engine

@st.cache_resource
def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

def create_tables():
    """Run once to create tables from your models."""
    Base.metadata.create_all(get_engine())