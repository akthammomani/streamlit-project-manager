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
import base64
from pathlib import Path
from PIL import Image
import os

import db

# ------------------ App chrome ------------------
st.set_page_config(
    page_title="Strivio - Project Manager",
    page_icon="logo_1.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
  [data-testid="stImage"] img { display:block; margin:auto; }
</style>
""", unsafe_allow_html=True)

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

def _norm_status(s: str) -> str:
    if not s:
        return "To-Do"
    s = str(s).strip().lower()
    mapping = {
        "todo": "To-Do", "to-do": "To-Do", "to do": "To-Do",
        "in-progress": "In Progress", "in progress": "In Progress", "inprogress": "In Progress",
        "done": "Done",
    }
    return mapping.get(s, s.title())

# ORM-safe shims
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

# ------------------ Centered login / project gate ------------------
def centered_logo(path: str = "logo_1.png", width: int = 160) -> None:
    p = Path(path)
    if not p.is_file():
        p = Path(__file__).with_name(path)
    try:
        b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
        st.markdown(
            f"<div style='text-align:center'><img src='data:image/png;base64,{b64}' style='width:{width}px;max-width:100%;height:auto;'/></div>",
            unsafe_allow_html=True,
        )
    except Exception:
        st.image(str(p), width=width)

def full_screen_login():
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display:none !important; }
      .main > div { padding-top: 6vh !important; }
    </style>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        centered_logo("logo_1.png", width=180)
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

def full_screen_project_gate(user_email: str):
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display:none !important; }
      .main > div { padding-top: 4vh !important; }
    </style>
    """, unsafe_allow_html=True)
    projects = db.get_projects_for_user(user_email)
    _, col, _ = st.columns([1, 2.6, 1])
    with col:
        centered_logo("logo_1.png", width=140)
        st.markdown("<h2 style='text-align:center;margin-top:8px;'>Choose or Create a Project</h2>", unsafe_allow_html=True)
        if projects:
            opt = st.selectbox("Open existing project", options=[f"{p.id} · {p.name}" for p in projects], key="center_open_select")
            if st.button("Open project", width='stretch'):
                sel_id = int(opt.split("·")[0].strip())
                st.session_state["selected_project_id"] = sel_id
                force_rerun()
        st.markdown("---")
        with st.form("center_new_project", clear_on_submit=True):
            p_name = st.text_input("Project name", placeholder="AI-Powered Apple Leaf Specialist")
            c1, c2 = st.columns(2)
            with c1: p_start = st.date_input("Start", value=date.today(), key="center_p_start")
            with c2: p_end   = st.date_input("End",   value=date.today(), key="center_p_end")
            c3, c4 = st.columns(2)
            with c3: is_public = st.checkbox("Public project (no PIN required)", value=False, key="center_public")
            with c4: pin_val   = st.text_input("Project PIN", type="password", disabled=is_public, key="center_pin")
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
                st.session_state["selected_project_id"] = pid
                st.success(f"Project created (id {pid}).")
                force_rerun()

# Login gate
user = st.session_state.get("user")
if not user:
    full_screen_login()
    st.stop()

# Project gate
if not st.session_state.get("selected_project_id"):
    full_screen_project_gate(user["email"])
    st.stop()

# ------------------ Sidebar after login ------------------
def load_logo(path="logo_1.png"):
    return Image.open(path)

with st.sidebar:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,3,1])
    with c2: st.image(load_logo(), width='stretch')
    st.caption(f"Signed in as **{user['email']}**")
    st.markdown("---")

_projects_raw = db.get_projects_for_user(user["email"])
current_project = next((p for p in _projects_raw if p.id == st.session_state.get("selected_project_id")), None)
if not current_project:
    st.session_state["selected_project_id"] = None
    force_rerun()

with st.sidebar:
    st.subheader("Projects")
    proj_names = [f"{p.id} · {p.name}" for p in _projects_raw]
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

st.title(current_project.name)
st.caption(f"{current_project.start_date} → {current_project.end_date}")

# PIN
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

# Roles
role = db.get_user_role(current_project.id, user["email"]) or "viewer"
CAN_WRITE = role in ("owner", "editor")
IS_OWNER  = role == "owner"

with st.sidebar.expander("Manage current project"):
    if IS_OWNER:
        new_name = st.text_input("Rename project", value=current_project.name, key="rename_proj")
        colA, colB = st.columns(2)
        with colA:
            if st.button("Save name", key="save_project_name"):
                db.rename_project(current_project.id, new_name)
                st.success("Project renamed."); force_rerun()
        with colB:
            if st.button("Delete project", type="secondary", key="delete_project_btn"):
                db.delete_project(current_project.id)
                st.session_state["selected_project_id"] = None
                st.success("Project deleted."); force_rerun()
    else:
        st.caption("Only the owner can manage this project.")

# ------------------ Tabs ------------------
tab1, tab2, tab3 = st.tabs(["Tasks", "Gantt", "Members"])

# ------------------ TASKS (inline editing) ------------------
with tab1:
    st.subheader("Tasks")

    # Get tasks (as dicts) and prepare editable DataFrame (index = id, hidden)
    raw_tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    # sort by start date (None last)
    raw_tasks.sort(key=lambda x: (x["start_date"] is None, x["start_date"]))

    if not raw_tasks and not CAN_WRITE:
        st.info("No tasks yet.")
    else:
        cols = ["Task","Status","Start","End","Assignee","Progress%","Description"]
        records = []
        for t in raw_tasks:
            records.append({
                "Task": t["name"] or "",
                "Status": _norm_status(t["status"]) if t["status"] else "To-Do",
                "Start": t["start_date"],
                "End": t["end_date"],
                "Assignee": t["assignee_email"] or "",
                "Progress%": float(round(t["progress"] or 0, 1)),
                "Description": "",  # you can persist this if you add to DB
            })

        df_tasks = pd.DataFrame(records, index=[t["id"] for t in raw_tasks])
        df_tasks.index.name = "id"

        if CAN_WRITE:
            edited = st.data_editor(
                df_tasks,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,  # hide id from UI
                column_config={
                    "Task": st.column_config.TextColumn("Task", required=True),
                    "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
                    "Start": st.column_config.DateColumn("Start"),
                    "End": st.column_config.DateColumn("End"),
                    "Assignee": st.column_config.TextColumn("Assignee"),
                    "Progress%": st.column_config.ProgressColumn(
                        "Progress", format="%d%%", min_value=0, max_value=100
                    ),
                    "Description": st.column_config.TextColumn("Description", help="Optional"),
                },
                column_order=cols,
                key="tasks_editor",
            )

            # Save changes button
            if st.button("💾 Save task changes", width="stretch"):
                try:
                    before_ids = set(df_tasks.index.astype("Int64").tolist())
                    after_ids  = set(edited.index.astype("Int64").tolist())

                    # Deleted rows
                    for removed_id in [i for i in before_ids if i not in after_ids and pd.notna(i)]:
                        db.delete_task(int(removed_id))

                    # Updated rows (existing id present & any difference)
                    inter = [i for i in before_ids.intersection(after_ids) if pd.notna(i)]
                    for i in inter:
                        orig = df_tasks.loc[i]
                        new  = edited.loc[i]
                        if not orig.equals(new):
                            name = str(new["Task"]).strip()
                            status = _norm_status(new["Status"])
                            start  = parse_date(new["Start"])
                            end    = parse_date(new["End"])
                            assg   = str(new["Assignee"]).strip() or None
                            prog   = float(new["Progress%"] or 0)
                            db.add_or_update_task(
                                project_id=current_project.id,
                                name=name,
                                status=status if status in STATUS_OPTIONS else "To-Do",
                                start=start, end=end,
                                assignee_email=assg,
                                description=str(new.get("Description","")).strip() or None,
                                task_id=int(i),
                                progress=float(max(0, min(100, prog))),
                            )

                    # Added rows (id is NaN)
                    new_rows = edited.loc[edited.index.isna()] if edited.index.hasnans else pd.DataFrame(columns=cols)
                    for _, r in new_rows.iterrows():
                        name = str(r["Task"]).strip()
                        if not name:
                            continue
                        status = _norm_status(r["Status"])
                        start  = parse_date(r["Start"])
                        end    = parse_date(r["End"])
                        assg   = str(r["Assignee"]).strip() or None
                        prog   = float(r["Progress%"] or 0)
                        db.add_or_update_task(
                            project_id=current_project.id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start, end=end,
                            assignee_email=assg,
                            description=str(r.get("Description","")).strip() or None,
                            task_id=None,
                            progress=float(max(0, min(100, prog))),
                        )

                    st.success("Tasks saved.")
                    force_rerun()
                except Exception as e:
                    st.error(f"Failed to save tasks: {e}")

            # Import CSV only (no download / no delete buttons)
            up = st.file_uploader(
                "Import tasks from CSV (Task, Status, Start, End, Assignee, Progress%, Description)",
                type=["csv"], key="tasks_csv_import"
            )
            if up is not None:
                try:
                    imp = pd.read_csv(up)
                    created = 0
                    for _, r in imp.iterrows():
                        name = str(r.get("Task","")).strip()
                        if not name:
                            continue
                        status = _norm_status(r.get("Status","To-Do"))
                        start  = parse_date(r.get("Start"))
                        end    = parse_date(r.get("End"))
                        assg   = str(r.get("Assignee","")).strip() or None
                        try:
                            prog = float(r.get("Progress%", 0) or 0)
                        except Exception:
                            prog = 0.0
                        desc = str(r.get("Description","")).strip() or None
                        db.add_or_update_task(
                            project_id=current_project.id,
                            name=name, status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start, end=end, assignee_email=assg,
                            description=desc, task_id=None,
                            progress=float(max(0, min(100, prog))),
                        )
                        created += 1
                    st.success(f"Imported {created} task(s).")
                    force_rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

        else:
            st.dataframe(
                df_tasks,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Progress%": st.column_config.ProgressColumn("Progress", format="%d%%", min_value=0, max_value=100)
                },
                column_order=cols,
            )

    st.markdown("---")
    # ------------------ SUBTASKS (inline editing) ------------------
    st.subheader("Subtasks")

    # choose a task for subtasks view
    tasks_for_select = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    if not tasks_for_select:
        st.caption("Create a task first to add subtasks.")
    else:
        # Sort by Start for the picker, too
        tasks_for_select.sort(key=lambda x: (x["start_date"] is None, x["start_date"]))
        pick = st.selectbox("Task", [f"{t['id']} · {t['name']}" for t in tasks_for_select], key="subtask_task_picker")
        picked_task_id = int(pick.split("·")[0].strip())

        raw_subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(picked_task_id)]
        raw_subs.sort(key=lambda x: (x["start_date"] is None, x["start_date"]))

        cols_sub = ["Subtask","Status","Start","End","Assignee","Progress%"]
        records_sub = []
        for s_ in raw_subs:
            records_sub.append({
                "Subtask": s_["name"] or "",
                "Status": _norm_status(s_["status"]) if s_["status"] else "To-Do",
                "Start": s_["start_date"],
                "End": s_["end_date"],
                "Assignee": s_["assignee_email"] or "",
                "Progress%": float(round(s_["progress"] or 0, 1)),
            })
        df_subs = pd.DataFrame(records_sub, index=[s["id"] for s in raw_subs])
        df_subs.index.name = "id"

        if CAN_WRITE:
            edited_subs = st.data_editor(
                df_subs,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Subtask": st.column_config.TextColumn("Subtask", required=True),
                    "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
                    "Start": st.column_config.DateColumn("Start"),
                    "End": st.column_config.DateColumn("End"),
                    "Assignee": st.column_config.TextColumn("Assignee"),
                    "Progress%": st.column_config.ProgressColumn("Progress", format="%d%%", min_value=0, max_value=100),
                },
                column_order=cols_sub,
                key=f"subs_editor_{picked_task_id}",
            )

            if st.button("💾 Save subtask changes", width="stretch", key=f"save_subs_{picked_task_id}"):
                try:
                    b_ids = set(df_subs.index.astype("Int64").tolist())
                    a_ids = set(edited_subs.index.astype("Int64").tolist())

                    # Deleted
                    for removed_id in [i for i in b_ids if i not in a_ids and pd.notna(i)]:
                        db.delete_subtask(int(removed_id))

                    # Updated
                    inter = [i for i in b_ids.intersection(a_ids) if pd.notna(i)]
                    for i in inter:
                        orig = df_subs.loc[i]
                        new  = edited_subs.loc[i]
                        if not orig.equals(new):
                            name = str(new["Subtask"]).strip()
                            status = _norm_status(new["Status"])
                            start  = parse_date(new["Start"])
                            end    = parse_date(new["End"])
                            assg   = str(new["Assignee"]).strip() or None
                            prog   = float(new["Progress%"] or 0)
                            db.add_or_update_subtask(
                                task_id=picked_task_id,
                                name=name,
                                status=status if status in STATUS_OPTIONS else "To-Do",
                                start=start, end=end,
                                assignee_email=assg,
                                subtask_id=int(i),
                                progress=float(max(0, min(100, prog))),
                            )

                    # Added
                    new_rows = edited_subs.loc[edited_subs.index.isna()] if edited_subs.index.hasnans else pd.DataFrame(columns=cols_sub)
                    for _, r in new_rows.iterrows():
                        name = str(r["Subtask"]).strip()
                        if not name:
                            continue
                        status = _norm_status(r["Status"])
                        start  = parse_date(r["Start"])
                        end    = parse_date(r["End"])
                        assg   = str(r["Assignee"]).strip() or None
                        prog   = float(r["Progress%"] or 0)
                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start, end=end,
                            assignee_email=assg,
                            subtask_id=None,
                            progress=float(max(0, min(100, prog))),
                        )

                    st.success("Subtasks saved.")
                    force_rerun()
                except Exception as e:
                    st.error(f"Failed to save subtasks: {e}")

            up_sub = st.file_uploader(
                "Import subtasks from CSV for selected task (Subtask, Status, Start, End, Assignee, Progress%)",
                type=["csv"], key=f"subs_csv_{picked_task_id}"
            )
            if up_sub is not None:
                try:
                    imp = pd.read_csv(up_sub)
                    created = 0
                    for _, r in imp.iterrows():
                        name = str(r.get("Subtask","")).strip()
                        if not name:
                            continue
                        status = _norm_status(r.get("Status","To-Do"))
                        start  = parse_date(r.get("Start"))
                        end    = parse_date(r.get("End"))
                        assg   = str(r.get("Assignee","")).strip() or None
                        try:
                            prog = float(r.get("Progress%", 0) or 0)
                        except Exception:
                            prog = 0.0
                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name, status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start, end=end, assignee_email=assg,
                            subtask_id=None, progress=float(max(0, min(100, prog))),
                        )
                        created += 1
                    st.success(f"Imported {created} subtask(s).")
                    force_rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

        else:
            st.dataframe(
                df_subs,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Progress%": st.column_config.ProgressColumn("Progress", format="%d%%", min_value=0, max_value=100)
                },
                column_order=cols_sub,
            )

# ------------------ GANTT ------------------
with tab2:
    st.subheader("Timeline (Gantt)")
    tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    rows = []
    for t in tasks:
        if t["start_date"] and t["end_date"]:
            rows.append({
                "Item": f"Task · {t['name']}",
                "Start": t["start_date"], "Finish": t["end_date"],
                "Status": _norm_status(t["status"]), "Assignee": t["assignee_email"],
                "Progress": round(t["progress"] or 0, 1),
            })
        subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(t["id"])]
        for s in subs:
            if s["start_date"] and s["end_date"]:
                rows.append({
                    "Item": f"Subtask · {s['name']}",
                    "Start": s["start_date"], "Finish": s["end_date"],
                    "Status": _norm_status(s["status"]), "Assignee": s["assignee_email"],
                    "Progress": round(s["progress"] or 0, 1),
                })
    if not rows:
        st.info("Add start/end dates to tasks or subtasks to see them on the Gantt.")
    else:
        df = pd.DataFrame(rows)
        df["Status"] = df["Status"].replace({
            "In-Progress": "In Progress", "in-pogress": "In Progress",
            "todo": "To-Do", "to do": "To-Do", "done": "Done"
        })
        status_colors = {
            "To-Do": "#9CA3AF", "In Progress": "#2563EB", "Done": "#10B981"
        }
        df["Status"] = pd.Categorical(df["Status"], categories=list(status_colors.keys()), ordered=True)
        fig = px.timeline(
            df, x_start="Start", x_end="Finish", y="Item",
            color="Status", hover_data=["Status","Assignee","Progress"],
            color_discrete_map=status_colors,
        )
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=30), legend_title_text="Status")
        st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "responsive": True})

# ------------------ Members ------------------
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
