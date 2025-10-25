# main.py
import streamlit as st

def force_rerun():
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

import base64
from pathlib import Path

def centered_logo(path: str = "logo_1.png", width: int = 160) -> None:
    """
    Renders a centered logo using base64 (works regardless of Streamlit wrappers).
    Falls back to st.image if the file can't be read.
    """
    p = Path(path)
    if not p.is_file():
        # try relative to this file
        p = Path(__file__).with_name(path)

    try:
        b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
        html = (
            f'<div style="text-align:center;">'
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:{width}px;max-width:100%;height:auto;" />'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        # graceful fallback if file missing
        st.image(str(p), width=width, caption=None)



# --- App chrome ---
st.set_page_config(
    page_title="Strivio - Project Manager",
    page_icon="logo_1.png",
    layout="wide",
    initial_sidebar_state="collapsed"  # collapsed until login / project selection
)

# Center all st.image images globally
st.markdown("""
<style>
  /* center images rendered by st.image */
  [data-testid="stImage"] img { 
    display: block; 
    margin-left: auto; 
    margin-right: auto; 
  }
</style>
""", unsafe_allow_html=True)


# ---------- helpers ----------
STATUS_OPTIONS = ["To-Do", "In Progress", "Done"]

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

# ---------- Full-screen login (before any sidebar UI) ----------
def full_screen_login():
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display: none !important; }
      .main > div { padding-top: 6vh !important; }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        # centered by the CSS rule above
        centered_logo("logo_1.png", width=180)
        #st.markdown("<h1 style='text-align:center;margin:10px 0 0 0;'>Strivio</h1>", unsafe_allow_html=True)
        #st.markdown("<p style='text-align:center;color:#6b7280;margin-top:4px;'>Simple, visual project management.</p>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Your email", placeholder="you@example.com")
            name  = st.text_input("Your name (optional)")
            submitted = st.form_submit_button("Sign in / Continue", width='stretch')

        if submitted:
            if not email:
                st.warning("Please enter your email.")
            else:
                st.session_state["user"] = db.login(email, name)
                force_rerun()

# ---------- Centered project gate (stay centered until a project is chosen/created) ----------
def full_screen_project_gate(user_email: str):
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display: none !important; }
      .main > div { padding-top: 4vh !important; }
    </style>
    """, unsafe_allow_html=True)

    projects = db.get_projects_for_user(user_email)

    _, col, _ = st.columns([1, 2.6, 1])
    with col:
        # centered by the CSS rule above
        centered_logo("logo_1.png", width=140)
        st.markdown("<h2 style='text-align:center;margin-top:8px;'>Choose or Create a Project</h2>", unsafe_allow_html=True)

        # Open existing
        if projects:
            opt = st.selectbox(
                "Open existing project",
                options=[f"{p.id} · {p.name}" for p in projects],
                key="center_open_select"
            )
            if st.button("Open project", width='stretch'):
                sel_id = int(opt.split("·")[0].strip())
                st.session_state["selected_project_id"] = sel_id
                force_rerun()

        st.markdown("---")

        # Create new (same inputs as sidebar)
        with st.form("center_new_project", clear_on_submit=True):
            p_name = st.text_input("Project name", placeholder="AI-Powered Apple Leaf Specialist")
            c1, c2 = st.columns(2)
            with c1:
                p_start = st.date_input("Start", value=date.today(), key="center_p_start")
            with c2:
                p_end = st.date_input("End", value=date.today(), key="center_p_end")
            c3, c4 = st.columns(2)
            with c3:
                is_public = st.checkbox("Public project (no PIN required)", value=False, key="center_public")
            with c4:
                pin_val = st.text_input("Project PIN", type="password", disabled=is_public, key="center_pin")
            members_csv = st.text_area("Member emails (comma-separated)", placeholder="a@x.com, b@y.com", key="center_members")
            submit_new = st.form_submit_button("Create project", width='stretch')

        if submit_new:
            if not p_name:
                st.warning("Please enter a project name.")
            elif p_end < p_start:
                st.warning("End date must be after start date.")
            elif not is_public and not pin_val:
                st.warning("Private projects require a PIN.")
            else:
                members = [m.strip() for m in members_csv.split(",") if m.strip()]
                pid = db.create_project(user_email, p_name, p_start, p_end, members, is_public=is_public, pin=(pin_val or None))
                st.success(f"Project created (id {pid}).")
                st.session_state["selected_project_id"] = pid
                force_rerun()

# ---------- Login gate ----------
user = st.session_state.get("user")
if not user:
    full_screen_login()
    st.stop()

# ---------- Project gate (keep centered until a project is chosen/created) ----------
if not st.session_state.get("selected_project_id"):
    full_screen_project_gate(user["email"])
    st.stop()

# ---------- Sidebar (post-login & project ready) ----------
def load_logo(path="logo_1.png"):
    return Image.open(path)

with st.sidebar:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        st.image(load_logo(), width='stretch')
    st.caption(f"Signed in as **{user['email']}**")
    st.markdown("---")

# ---------- project selection / creation (optional switcher in sidebar) ----------
_projects_raw = db.get_projects_for_user(user["email"])

# Build current project from remembered selection
current_project = next((p for p in _projects_raw if p.id == st.session_state.get("selected_project_id")), None)
if not current_project:
    # session lost or project removed; go back to gate
    st.session_state["selected_project_id"] = None
    force_rerun()

with st.sidebar:
    st.subheader("Projects")
    proj_names = [f'{p.id} · {p.name}' for p in _projects_raw]
    # preselect current project
    try:
        default_label = f"{current_project.id} · {current_project.name}"
        idx = 0 if not proj_names else max(0, proj_names.index(default_label))
    except ValueError:
        idx = 0
    chosen = st.selectbox("Open project", options=proj_names, index=idx, key="sidebar_project_select")
    chosen_id = int(chosen.split("·")[0].strip())
    if chosen_id != current_project.id:
        st.session_state["selected_project_id"] = chosen_id
        force_rerun()

    with st.expander("New project"):
        p_name = st.text_input("Project name", placeholder="AI-Powered Apple Leaf Specialist", key="sb_p_name")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_start = st.date_input("Start", value=date.today(), key="sb_p_start")
        with col_p2:
            p_end = st.date_input("End", value=date.today(), key="sb_p_end")

        colx1, colx2 = st.columns(2)
        with colx1:
            is_public = st.checkbox("Public project (no PIN required)", value=False, key="sb_public")
        with colx2:
            pin_val = st.text_input(
                "Project PIN", type="password", disabled=is_public, key="sb_pin",
                help="Members will need this PIN to open the project."
            )

        members_csv = st.text_area("Member emails (comma-separated)", placeholder="a@x.com, b@y.com", key="sb_members")

        if st.button("Create project", width='stretch', key="sb_create"):
            if not p_name:
                st.warning("Please enter a project name.")
            elif p_end < p_start:
                st.warning("End date must be after start date.")
            elif not is_public and not pin_val:
                st.warning("Private projects require a PIN.")
            else:
                members = [m.strip() for m in members_csv.split(",") if m.strip()]
                pid = db.create_project(
                    user["email"], p_name, p_start, p_end, members,
                    is_public=is_public, pin=(pin_val or None)
                )
                st.session_state["selected_project_id"] = pid
                st.success(f"Project created (id {pid}).")
                force_rerun()

st.title(current_project.name)
st.caption(f"{current_project.start_date} → {current_project.end_date}")

# Require PIN for private projects (one-time per session)
pin_key = f"pin_ok_{current_project.id}"
if not getattr(current_project, "is_public", True) and not st.session_state.get(pin_key):
    with st.sidebar.expander("🔒 Enter project PIN to view"):
        entered_pin = st.text_input("Project PIN", type="password", key=f"pin_in_{current_project.id}")
        if st.button("Unlock", key=f"unlock_{current_project.id}"):
            if db.check_project_pin(current_project.id, entered_pin):
                st.session_state[pin_key] = True
                force_rerun()
            else:
                st.error("Incorrect PIN.")
    st.stop()

# Role flags
role = db.get_user_role(current_project.id, user["email"]) or "viewer"
CAN_WRITE = role in ("owner", "editor")
IS_OWNER  = role == "owner"

# Manage project (owner only)
with st.sidebar.expander("Manage current project"):
    if IS_OWNER:
        new_name = st.text_input("Rename project", value=current_project.name, key="rename_proj")
        colA, colB = st.columns(2)
        with colA:
            if st.button("Save name", key="save_project_name"):
                db.rename_project(current_project.id, new_name)
                st.success("Project renamed.")
                force_rerun()
        with colB:
            if st.button("Delete project", type="secondary", key="delete_project_btn"):
                db.delete_project(current_project.id)
                st.success("Project deleted.")
                # clear selection and return to project gate
                st.session_state["selected_project_id"] = None
                force_rerun()
    else:
        st.caption("Only the owner can manage this project.")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["Tasks", "Gantt", "Members"])

# ---------- Tasks Tab ----------
with tab1:
    st.subheader("Tasks")

    tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]

    if not CAN_WRITE:
        st.info("You have read-only access to this project.")

    # Create / Edit Task (writers only)
    if CAN_WRITE:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Add / Edit Task**")
        with col2:
            pass

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


# ---------- Task List (visible to all) ----------
def _norm_status(s: str) -> str:
    if not s:
        return "To-Do"
    s = str(s).strip().lower()
    mapping = {
        "todo": "To-Do",
        "to-do": "To-Do",
        "to do": "To-Do",
        "in-progress": "In Progress",
        "in progress": "In Progress",
        "inprogress": "In Progress",
        "done": "Done",
    }
    return mapping.get(s, s.title())

if tasks:
    st.markdown("**Your Tasks**")

    task_rows = [{
        "id": t["id"],
        "Task": t["name"],
        "Status": _norm_status(t["status"]),
        "Start": t["start_date"],
        "End": t["end_date"],
        "Assignee": t["assignee_email"],
        "Progress%": float(round(t["progress"], 1)),
        "Description": ""  # optional placeholder for CSV template
    } for t in tasks]

    df_tasks = pd.DataFrame(task_rows, columns=["id","Task","Status","Start","End","Assignee","Progress%","Description"])

    st.dataframe(
        df_tasks,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.TextColumn("id", help="Internal id", width="small"),
            "Task": st.column_config.TextColumn("Task", required=True),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, disabled=True),
            "Start": st.column_config.DateColumn("Start"),
            "End": st.column_config.DateColumn("End"),
            "Assignee": st.column_config.TextColumn("Assignee"),
            "Progress%": st.column_config.ProgressColumn(
                "Progress",
                help="Completion %",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
            "Description": st.column_config.TextColumn("Description", help="Optional", width="medium"),
        },
        column_order=["Task","Status","Start","End","Assignee","Progress%","Description","id"],
    )

    col_dl, col_tpl, col_up = st.columns([1,1,2])
    with col_dl:
        st.download_button(
            "⬇️ Download tasks CSV",
            data=df_tasks.drop(columns=["id"]).to_csv(index=False).encode("utf-8"),
            file_name=f"tasks_project_{current_project.id}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_tpl:
        # clean, empty template users can fill
        template_tasks = pd.DataFrame(
            columns=["Task","Status","Start","End","Assignee","Progress%","Description"]
        )
        st.download_button(
            "📄 Task CSV template",
            data=template_tasks.to_csv(index=False).encode("utf-8"),
            file_name="task_import_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_up:
        up = st.file_uploader(
            "Import tasks from CSV",
            type=["csv"],
            accept_multiple_files=False,
            key="task_csv_import",
            help="Columns: Task, Status, Start, End, Assignee, Progress%, Description",
        )
        if up is not None and CAN_WRITE:
            try:
                imp = pd.read_csv(up)
                created = 0
                for _, r in imp.iterrows():
                    name = str(r.get("Task", "")).strip()
                    if not name:
                        continue
                    status = _norm_status(r.get("Status", "To-Do"))
                    start = parse_date(r.get("Start"))
                    end   = parse_date(r.get("End"))
                    assg  = str(r.get("Assignee", "")).strip() or None
                    try:
                        prog = float(r.get("Progress%", 0) or 0)
                    except Exception:
                        prog = 0.0
                    desc  = str(r.get("Description", "")).strip() or None

                    db.add_or_update_task(
                        project_id=current_project.id,
                        name=name,
                        status=status if status in STATUS_OPTIONS else "To-Do",
                        start=start,
                        end=end,
                        assignee_email=assg,
                        description=desc,
                        task_id=None,
                        progress=float(max(0, min(100, prog))),
                    )
                    created += 1
                st.success(f"Imported {created} task(s).")
                force_rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")
else:
    st.info("No tasks yet. Add your first task above." if CAN_WRITE else "No tasks yet.")



    # Delete Task (writers only)
    if CAN_WRITE and tasks:
        st.markdown("**Delete Task**")
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

    # Subtasks
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

        # Subtask form (writers only)
        if CAN_WRITE:
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

    # Subtasks table (visible to all)
# Subtasks table (visible to all)
    if subs:
        sub_rows = [{
            "id": s["id"],
            "Subtask": s["name"],
            "Status": _norm_status(s["status"]),
            "Start": s["start_date"],
            "End": s["end_date"],
            "Assignee": s["assignee_email"],
            "Progress%": float(round(s["progress"], 1)),
        } for s in subs]
        df_subs = pd.DataFrame(sub_rows, columns=["id","Subtask","Status","Start","End","Assignee","Progress%"])
    
        st.dataframe(
            df_subs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("id", help="Internal id", width="small"),
                "Subtask": st.column_config.TextColumn("Subtask", required=True),
                "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS, disabled=True),
                "Start": st.column_config.DateColumn("Start"),
                "End": st.column_config.DateColumn("End"),
                "Assignee": st.column_config.TextColumn("Assignee"),
                "Progress%": st.column_config.ProgressColumn(
                    "Progress",
                    help="Completion %",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            column_order=["Subtask","Status","Start","End","Assignee","Progress%","id"],
        )
    
        cdl, ctpl, cup = st.columns([1,1,2])
        with cdl:
            st.download_button(
                "⬇️ Download subtasks CSV",
                data=df_subs.drop(columns=["id"]).to_csv(index=False).encode("utf-8"),
                file_name=f"subtasks_task_{picked_task_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with ctpl:
            template_subs = pd.DataFrame(
                columns=["Subtask","Status","Start","End","Assignee","Progress%"]
            )
            st.download_button(
                "📄 Subtask CSV template",
                data=template_subs.to_csv(index=False).encode("utf-8"),
                file_name="subtask_import_template.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with cup:
            up_sub = st.file_uploader(
                "Import subtasks from CSV (for selected task)",
                type=["csv"],
                accept_multiple_files=False,
                key=f"sub_csv_import_{picked_task_id}",
                help="Columns: Subtask, Status, Start, End, Assignee, Progress%",
            )
            if up_sub is not None and CAN_WRITE:
                try:
                    imp = pd.read_csv(up_sub)
                    created = 0
                    for _, r in imp.iterrows():
                        name = str(r.get("Subtask", "")).strip()
                        if not name:
                            continue
                        status = _norm_status(r.get("Status", "To-Do"))
                        start = parse_date(r.get("Start"))
                        end   = parse_date(r.get("End"))
                        assg  = str(r.get("Assignee", "")).strip() or None
                        try:
                            prog = float(r.get("Progress%", 0) or 0)
                        except Exception:
                            prog = 0.0
    
                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start,
                            end=end,
                            assignee_email=assg,
                            subtask_id=None,
                            progress=float(max(0, min(100, prog))),
                        )
                        created += 1
                    st.success(f"Imported {created} subtask(s).")
                    force_rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")




        # Delete Subtask (writers only)
        if CAN_WRITE and subs:
            st.markdown("**Delete Subtask**")
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
        df["Status"] = df["Status"].replace({
        "In-Progress": "In Progress",
        "in-pogress": "In Progress",
        "todo": "To-Do",
        "to do": "To-Do",
        "done": "Done"
       })

        status_colors = {
        "To-Do":      "#9CA3AF",  # Gray
        "In Progress":"#2563EB",  # blue
        "Done":       "#10B981",  # green
        }

        df["Status"] = pd.Categorical(df["Status"], categories=list(status_colors.keys()), ordered=True)
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Item",
            color="Status",
            hover_data=["Status", "Assignee", "Progress"],
            color_discrete_map=status_colors,
        )
        #fig.update_yaxes(autorange="reversed")
        
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=30),legend_title_text="Status")
        plotly_config = {"displaylogo": False,"responsive": True}
        st.plotly_chart(fig, width="stretch", config=plotly_config)

# ---------- Members Tab ----------
with tab3:
    st.subheader("Project Members")
    if not CAN_WRITE:
        st.info("Read-only members cannot manage users.")
    else:
        members_line = st.text_area("Add members by email (comma-separated)")
        role_choice = st.selectbox("Role for new members", ["viewer", "editor"])
        if st.button("Add Members"):
            emails = [e.strip() for e in members_line.split(",") if e.strip()]
            if not emails:
                st.warning("No valid emails.")
            else:
                import db as _db
                with _db.SessionLocal() as s:
                    for e in emails:
                        _db.set_member_role(current_project.id, e, role_choice)
                st.success(f"Added/updated {len(emails)} member(s) as {role_choice}.")
                force_rerun()
