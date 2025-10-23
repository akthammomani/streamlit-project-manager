# ui/projects_panel.py

import streamlit as st
from datetime import date
import pandas as pd
from sqlmodel import select

from db import get_session
from models.project import Project
from models.project_member import ProjectMember

# ✅ Optional (not strictly required, but helps static checkers and IDEs)
__all__ = ["render_projects", "render_new_project"]


def render_projects(current_user_id: int = None):
    """Display a dropdown of projects the user belongs to and return selected project_id."""
    if current_user_id is None:
        current_user_id = st.session_state.get("user_id")

    st.subheader("Projects (only ones you belong to)")

    with get_session() as s:
        memberships = s.exec(
            select(ProjectMember).where(ProjectMember.user_id == current_user_id)
        ).all()

        project_ids = [m.project_id for m in memberships]
        projects = s.exec(select(Project).where(Project.id.in_(project_ids))).all() if project_ids else []

    if not projects:
        st.info("You don't belong to any projects yet.")
        return None

    proj_options = {f"{p.name} (#{p.id})": p.id for p in projects}
    selected_label = st.selectbox("Select a project", ["—"] + list(proj_options.keys()))
    return proj_options.get(selected_label)


def render_new_project(current_user_id: int):
    """Form to create a new project."""
    st.subheader("New Project")

    with st.form("new_project"):
        p_name = st.text_input("Project name", placeholder="AI‑Powered Apple Leaf Specialist")
        p_desc = st.text_area("Description", placeholder="Short project description…")
        p_start = st.date_input("Start", value=date.today())
        p_end = st.date_input("End", value=date.today())
        submitted = st.form_submit_button("Create project")

        if submitted and p_name:
            with get_session() as s:
                p = Project(name=p_name, description=p_desc, start_date=p_start, end_date=p_end)
                s.add(p)
                s.commit()
                s.refresh(p)

                s.add(ProjectMember(project_id=p.id, user_id=current_user_id, role="owner"))
                s.commit()

            st.success(f"Created project #{p.id} — join code: {p.join_code}")
