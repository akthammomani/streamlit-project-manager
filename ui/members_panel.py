# ui/members_panel.py
import streamlit as st
import pandas as pd

from db import get_session
from models.project_member import ProjectMember
from models.user import User

def render_members_panel(project_id: int, current_user_id: int):
    st.subheader("Project Members")
    role = member_role(current_user_id, project_id)
    can_manage = role in {"owner", "member"}
    if can_manage:
        with st.form("invite_member"):
            inv_email = st.text_input("Invite by email")
            role_new = st.selectbox("Role", ["member", "owner", "viewer"], index=0)
            add_btn = st.form_submit_button("Add")
        if add_btn and inv_email:
            u = upsert_user(inv_email)
            with get_session() as s:
                s.add(ProjectMember(project_id=project_id, user_id=u.id, role=role_new))
                s.commit()
            st.success(f"Added {inv_email} as {role_new}")

    with get_session() as s:
        rows = s.exec(select(ProjectMember).where(ProjectMember.project_id == project_id)).all()
        data = [{"Email": s.get(User, r.user_id).email,
                 "Name": s.get(User, r.user_id).name,
                 "Role": r.role}
                for r in rows]
    st.dataframe(pd.DataFrame(data) if data else pd.DataFrame(columns=["Email", "Name", "Role"]))
