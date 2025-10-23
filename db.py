# db.py
import os
import streamlit as st
from sqlmodel import SQLModel, Session, create_engine

# ✅ Use environment variable or default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pm.db")

@st.cache_resource
def get_engine():
    """Return a cached SQLAlchemy engine for Streamlit."""
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    """Create a new SQLModel session."""
    return Session(get_engine())

def init_db():
    """Initialize database (create tables once)."""
    # ✅ Import all models explicitly to register them
    import models  # triggers import of all models from __init__.py

    engine = get_engine()

    # ✅ Clear old metadata to prevent redefinition errors
    SQLModel.metadata.clear()

    # ✅ Create all tables
    SQLModel.metadata.create_all(engine, checkfirst=True)
