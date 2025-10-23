# ui/admin_panel.py
import streamlit as st
import os

from db import get_session
from models.project import Project

def render_admin_panel(project_id: int, current_user_id: int):
    st.subheader("Admin Tools")
    # only owner
    role = member_role(current_user_id, project_id)
    if role != "owner":
        st.info("Owner‑only area")
        return

    if st.button("Rotate join code"):
        with get_session() as s:
            p = s.get(Project, project_id)
            p.join_code = os.urandom(3).hex()
            s.add(p); s.commit(); s.refresh(p)
        st.success(f"New join code: {p.join_code}")

    st.markdown("**Danger zone**")
    if st.button("Delete project (irreversible)"):
        with get_session() as s:
            subs = s.exec(select(Subtask).join(Task).where(Task.project_id == project_id)).all()
            for sub in subs: s.delete(sub)
            assns = s.exec(select(TaskAssignee).join(Task).where(Task.project_id == project_id)).all()
            for a in assns: s.delete(a)
            tasks = s.exec(select(Task).where(Task.project_id == project_id)).all()
            for t in tasks: s.delete(t)
            members = s.exec(select(ProjectMember).where(ProjectMember.project_id == project_id)).all()
            for m in members: s.delete(m)
            s.delete(s.get(Project, project_id))
            s.commit()
        st.success("Project deleted")
