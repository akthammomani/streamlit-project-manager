# db.py
from sqlmodel import SQLModel, create_engine, Session
import os, streamlit as st

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pm.db")

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, echo=True)  

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
