# main.py
import streamlit as st

def force_rerun():
    # works on old & new Streamlit
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()
    else:
        st.warning("Unable to rerun: your Streamlit version is too old.")

import pandas as pd
from datetime import date
from dateutil import parser
import plotly.express as px

import db

from PIL import Image
import os

st.set_page_config(page_title="Project Manager", layout="wide")

# ---------- helpers ----------
STATUS_OPTIONS = ["Backlog", "In-Progress", "Completed"]

def parse_date(x):
    if not x:
        return None
    if isinstance(x, date):
        return x
    try:
        return parser.parse(str(x)).date()
    except Exception:
        return None

# --- compatibility shims so UI never touches lazy ORM attrs ---
def _to_task_dict(t):
    if isinstance(t, dict):
        return t
    assignee_email = None
    if isinstance(getattr(t, "__dict__", {}), dict) and "assignee" in t.__dict__ and getattr(t.assignee, "email", None):
        assignee_email = t.assignee.email
    return {
        "id": getattr(t, "id", None),
        "name": getattr(t, "name", None),
        "status": getattr(t, "status", None),
        "start_date": getattr(t, "start_date", None),
        "end_date": getattr(t, "end_date", None),
        "progress": float(getattr(t, "progress", 0) or 0),
        "assignee_email": assignee_email,
    }

def _to_subtask_dict(s):
    if isinstance(s, dict):
        return s
    assignee_email = None
    if isinstance(getattr(s, "__dict__", {}), dict) and "assignee" in s.__dict__ and getattr(s.assignee, "email", None):
        assignee_email = s.assignee.email
    return {
        "id": getattr(s, "id", None),
        "name": getattr(s, "name", None),
        "status": getattr(s, "status", None),
        "start_date": getattr(s, "start_date", None),
        "end_date": getattr(s, "end_date", None),
        "progress": float(getattr(s, "progress", 0) or 0),
        "assignee_email": assignee_email,
    }

@st.cache_resource
def _init_db_once():
    db.init_db()
    return True

_init_db_once()

# ---------- auth (simple email "profile") ----------
@st.cache_data
def load_logo(path="logo_1.png"):
    return Image.open(path)
    
with st.sidebar:
    # optional: reduce top padding
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    # center using sidebar columns
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        st.image(load_logo(), use_container_width=True)  # or set width=140
    st.markdown("---")  # separator before the rest of the sidebar
    st.header("Profile")
    email = st.text_input("Your email", placeholder="you@example.com")
    name = st.text_input("Your name (optional)")
    login_btn = st.button("Sign in / Continue", use_container_width=True)

if login_btn:
    if not email:
        st.sidebar.error("Email is required.")
    else:
        st.session_state["user"] = db.login(email, name)

user = st.session_state.get("user")
if not user:
    st.info("Enter your email in the sidebar to continue.")
    st.stop()

# ---------- project selection / creation ----------
st.sidebar.markdown("---")
st.sidebar.subheader("Projects")
_projects_raw = db.get_projects_for_user(user["email"])
projects = _projects_raw  # only use id/name here
proj_names = [f'{p.id} · {p.name}' for p in projects]
selected = st.sidebar.selectbox("Open project", options=["—"] + proj_names, index=0)

with st.sidebar.expander("New project"):
    p_name = st.text_input("Project name", placeholder="AI-Powered Apple Leaf Specialist")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_start = st.date_input("Start", value=date.today())
    with col_p2:
        p_end = st.date_input("End", value=date.today())
    members_csv = st.text_area("Member emails (comma-separated)", placeholder="a@x.com, b@y.com")
    if st.button("Create project", use_container_width=True):
        if not p_name:
            st.warning("Please enter a project name.")
        elif p_end < p_start:
            st.warning("End date must be after start date.")
        else:
            members = [m.strip() for m in members_csv.split(",") if m.strip()]
            pid = db.create_project(user["email"], p_name, p_start, p_end, members)
            st.success(f"Project created (id {pid}).")
            force_rerun()

# Determine current project
current_project = None
if selected != "—" and projects:
    sel_id = int(selected.split("·")[0].strip())
    current_project = next((p for p in projects if p.id == sel_id), None)

if not current_project:
    st.info("Create or open a project from the sidebar.")
    st.stop()

st.title(current_project.name)
st.caption(f"{current_project.start_date} → {current_project.end_date}")

with st.sidebar.expander("Manage current project"):
    if current_project:
        new_name = st.text_input("Rename project", value=current_project.name, key="rename_proj")
        colA, colB = st.columns(2)
        with colA:
            if st.button("Save name"):
                db.rename_project(current_project.id, new_name)
                st.success("Project renamed.")
                force_rerun()
        with colB:
            if st.button("Delete project", type="secondary"):
                db.delete_project(current_project.id)
                st.success("Project deleted.")
                force_rerun()
    else:
        st.caption("Open a project first.")

tab1, tab2, tab3 = st.tabs(["Tasks", "Gantt", "Members"])

# ---------- Tasks Tab ----------
with tab1:
    st.subheader("Tasks")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Add / Edit Task**")
    with col2:
        pass

    # Normalize tasks to dicts so UI never touches lazy attributes
    tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]

    # Create / Edit Task
    with st.form("task_form", clear_on_submit=True):
        t_id = st.selectbox(
            "Edit existing (optional)",
            options=["New"] + [f"{t['id']} · {t['name']}" for t in tasks]
        )
        t_name = st.text_input("Task name")
        t_desc = st.text_area("Description", placeholder="What needs to be done?")
        c1, c2, c3 = st.columns(3)
        with c1:
            t_status = st.selectbox("Status", STATUS_OPTIONS, index=0)
        with c2:
            t_start = st.date_input("Start", value=date.today())
        with c3:
            t_end = st.date_input("End", value=date.today())
        c4, c5 = st.columns(2)
        with c4:
            t_assignee = st.text_input("Assignee email (optional)")
        with c5:
            t_prog = st.slider("Progress %", 0, 100, 0)
        submitted = st.form_submit_button("Save Task")

    if submitted:
        if not t_name:
            st.warning("Task name is required.")
        elif t_end and t_start and t_end < t_start:
            st.warning("Task end cannot be before start.")
        else:
            edit_id = None if t_id == "New" else int(t_id.split("·")[0].strip())
            db.add_or_update_task(
                project_id=current_project.id,
                name=t_name,
                status=t_status,
                start=t_start,
                end=t_end,
                assignee_email=t_assignee or None,
                description=t_desc or None,
                task_id=edit_id,
                progress=float(t_prog),
            )
            st.success("Task saved.")
            force_rerun()

    # List tasks with inline actions
    if tasks:
        st.markdown("**Your Tasks**")
        task_rows = []
        for t in tasks:
            task_rows.append({
                "id": t["id"],
                "Task": t["name"],
                "Status": t["status"],
                "Start": t["start_date"],
                "End": t["end_date"],
                "Assignee": t["assignee_email"],
                "Progress%": round(t["progress"], 1)
            })
        st.dataframe(pd.DataFrame(task_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No tasks yet. Add your first task above.")

    # --- DELETE TASK UI ---
    st.markdown("**Delete Task**")
    if tasks:
        del_task_opt = st.selectbox(
            "Select task to delete",
            [f"{t['id']} · {t['name']}" for t in tasks],
            key="del_task_opt"
        )
        if st.button("Delete Task", type="secondary", key="del_task_btn"):
            db.delete_task(int(del_task_opt.split("·")[0].strip()))
            st.success("Task deleted.")
            force_rerun()

    st.markdown("---")
    # Subtasks UI
    st.subheader("Subtasks")
    task_for_sub = st.selectbox(
        "Task",
        options=[f"{t['id']} · {t['name']}" for t in tasks] if tasks else [],
        key="task_picker_for_subtasks"
    )
    if not task_for_sub and not tasks:
        st.caption("Create a task first to add subtasks.")
    else:
        picked_task_id = int(task_for_sub.split("·")[0].strip())
        subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(picked_task_id)]

        with st.form("subtask_form", clear_on_submit=True):
            st_id = st.selectbox(
                "Edit existing (optional)",
                options=["New"] + [f"{s['id']} · {s['name']}" for s in subs]
            )
            st_name = st.text_input("Subtask name")
            c1, c2, c3 = st.columns(3)
            with c1:
                st_status = st.selectbox("Status", STATUS_OPTIONS, index=0)
            with c2:
                st_start = st.date_input("Start", value=date.today(), key="st_start")
            with c3:
                st_end = st.date_input("End", value=date.today(), key="st_end")
            c4, c5 = st.columns(2)
            with c4:
                st_assignee = st.text_input("Assignee email (optional)")
            with c5:
                st_prog = st.slider("Progress %", 0, 100, 0, key="st_prog")
            st_submit = st.form_submit_button("Save Subtask")

        if st_submit:
            if not st_name:
                st.warning("Subtask name is required.")
            elif st_end and st_start and st_end < st_start:
                st.warning("Subtask end cannot be before start.")
            else:
                edit_id = None if st_id == "New" else int(st_id.split("·")[0].strip())
                db.add_or_update_subtask(
                    task_id=picked_task_id,
                    name=st_name,
                    status=st_status,
                    start=st_start,
                    end=st_end,
                    assignee_email=st_assignee or None,
                    subtask_id=edit_id,
                    progress=float(st_prog),
                )
                st.success("Subtask saved.")
                force_rerun()

        if subs:
            sub_rows = []
            for s in subs:
                sub_rows.append({
                    "id": s["id"],
                    "Subtask": s["name"],
                    "Status": s["status"],
                    "Start": s["start_date"],
                    "End": s["end_date"],
                    "Assignee": s["assignee_email"],
                    "Progress%": round(s["progress"], 1)
                })
            st.dataframe(pd.DataFrame(sub_rows), use_container_width=True, hide_index=True)

        # --- DELETE SUBTASK UI ---
        st.markdown("**Delete Subtask**")
        if subs:
            del_sub_opt = st.selectbox(
                "Select subtask to delete",
                [f"{s['id']} · {s['name']}" for s in subs],
                key="del_sub_opt"
            )
            if st.button("Delete Subtask", type="secondary", key="del_sub_btn"):
                db.delete_subtask(int(del_sub_opt.split("·")[0].strip()))
                st.success("Subtask deleted.")
                force_rerun()

# ---------- Gantt Tab ----------
with tab2:
    st.subheader("Timeline (Gantt)")
    tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    rows = []
    for t in tasks:
        if t["start_date"] and t["end_date"]:
            rows.append({
                "Item": f"Task · {t['name']}",
                "Start": t["start_date"],
                "Finish": t["end_date"],
                "Status": t["status"],
                "Assignee": t["assignee_email"],
                "Progress": round(t["progress"], 1)
            })
        subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(t["id"])]
        for s in subs:
            if s["start_date"] and s["end_date"]:
                rows.append({
                    "Item": f"Subtask · {s['name']}",
                    "Start": s["start_date"],
                    "Finish": s["end_date"],
                    "Status": s["status"],
                    "Assignee": s["assignee_email"],
                    "Progress": round(s["progress"], 1)
                })
    if not rows:
        st.info("Add start/end dates to tasks or subtasks to see them on the Gantt.")
    else:
        df = pd.DataFrame(rows)
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Item",
                          hover_data=["Status", "Assignee", "Progress"], color="Status")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

# ---------- Members Tab ----------
with tab3:
    st.subheader("Project Members")
    members_line = st.text_area("Add members by email (comma-separated)")
    if st.button("Add Members"):
        emails = [e.strip() for e in members_line.split(",") if e.strip()]
        import db as _db
        with _db.SessionLocal() as s:
            proj = s.get(_db.Project, current_project.id)
            for e in emails:
                if not e:
                    continue
                u = _db._get_or_create_user(s, e)
                exists = s.query(_db.ProjectMember).filter(
                    _db.ProjectMember.project_id == proj.id,
                    _db.ProjectMember.user_id == u.id
                ).one_or_none()
                if not exists:
                    s.add(_db.ProjectMember(project_id=proj.id, user_id=u.id, role="member"))
            s.commit()
        st.success("Members added.")
        force_rerun()
