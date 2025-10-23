# ui/projects_panel.py
import streamlit as st
from datetime import date
import pandas as pd

from db import get_session
from models.project import Project
from models.project_member import ProjectMember
from models.user import User
from models.task import Task

def render_projects(current_user_id: int):
    st.subheader("Projects (only ones you belong to)")
    with get_session() as s:
        memberships = s.exec(
            select(ProjectMember).where(ProjectMember.user_id == current_user_id)
        ).all()
        project_ids = [m.project_id for m in memberships]
        projects = s.exec(
            select(Project).where(Project.id.in_(project_ids)).order_by(Project.id.desc())
        ).all() if project_ids else []
    project_map = {f"{p.name} (#{p.id})": p.id for p in projects}
    selected_label = st.selectbox("Select a project", ["—"] + list(project_map.keys()))
    selected_project_id = project_map.get(selected_label)
    return selected_project_id

def render_new_project(current_user_id: int):
    st.subheader("New Project")
    with st.form("new_project"):
        p_name = st.text_input("Project name", placeholder="AI‑Powered Apple Leaf Specialist")
        p_desc = st.text_area("Description", placeholder="Short project description…")
        p_start = st.date_input("Start", value=date.today())
        p_end = st.date_input("End", value=date.today())
        submitted = st.form_submit_button("Create project")
        if submitted and p_name:
            with get_session() as s:
                p = Project(name=p_name, description=p_desc,
                            start_date=p_start, end_date=p_end)
                s.add(p); s.commit(); s.refresh(p)
                s.add(ProjectMember(project_id=p.id, user_id=current_user_id, role="owner"))
                s.commit()
            st.success(f"Created project #{p.id} — join code: {p.join_code}")
