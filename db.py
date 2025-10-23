# db.py
import os
import streamlit as st
from sqlmodel import SQLModel, Session, create_engine

# ✅ Use environment variable or default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pm.db")

@st.cache_resource
def get_engine():
    """Return a cached SQLAlchemy engine (avoids reconnecting each reload)."""
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    """Get a new SQLModel Session."""
    return Session(get_engine())

def init_db():
    """Initialize database once — safe for Streamlit hot reload."""
    from models import (
        project,
        project_member,
        user,
        task,
        subtask,
        task_assignee,
    )  # ✅ ensure all models are imported before table creation

    engine = get_engine()

    # ✅ FIX: clear metadata before creating tables (prevents InvalidRequestError)
    SQLModel.metadata.clear()

    # ✅ create_all only once
    SQLModel.metadata.create_all(engine, checkfirst=True)
