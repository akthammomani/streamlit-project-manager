# main.py
import streamlit as st
from db import init_db
from ui.projects_panel import render_projects, render_new_project
from ui.members_panel import render_members_panel
from ui.tasks_panel import render_tasks_panel
from ui.gantt_panel import render_gantt_panel
from ui.import_export_panel import render_import_export
from ui.admin_panel import render_admin_panel
from utils.progress import compute_project_progress

init_db()
st.set_page_config(page_title="Project Manager", layout="wide")
st.title("📌 Project Management — Streamlit")

# Fake login (no auth)
with st.sidebar:
    st.subheader("Login")
    email = st.text_input("Your email")
    login = st.button("Sign in")
if login and email:
    st.session_state["user_email"] = email
    st.session_state["user_id"] = hash(email) % 999999

if "user_id" not in st.session_state:
    st.stop()

user_id = st.session_state["user_id"]
user_email = st.session_state["user_email"]

st.sidebar.markdown("---")
render_new_project(user_id)
project_id = render_projects(current_user_id)
if not project_id:
    st.stop()

st.markdown("## Dashboard")
st.metric("Progress", f"{compute_project_progress(project_id):.0f}%")

tabs = st.tabs(["Members", "Tasks", "Gantt", "Backup", "Admin"])
with tabs[0]: render_members_panel(project_id, user_id)
with tabs[1]: render_tasks_panel(project_id, user_id, user_email)
with tabs[2]: render_gantt_panel(project_id)
with tabs[3]: render_import_export(project_id, user_id)
with tabs[4]: render_admin_panel(project_id, user_id)
