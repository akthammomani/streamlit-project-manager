# db.py
import os
import streamlit as st
from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pm.db")

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL, echo=False)

def get_session():
    return Session(get_engine())

def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine, checkfirst=True)
