# main.py
import streamlit as st

def force_rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

import pandas as pd
from datetime import date
from dateutil import parser
import plotly.express as px
import base64
from pathlib import Path
from PIL import Image
import db

# --- App chrome ---
st.set_page_config(
    page_title="Strivio - Project Manager",
    page_icon="logo_1.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global CSS: hide index/ID column in all tables/editors (header + body)
st.markdown("""
<style>
div[data-testid="stDataFrame"] thead tr th:first-child,
div[data-testid="stDataFrame"] tbody tr td:first-child,
div[data-testid="stDataEditor"] thead tr th:first-child,
div[data-testid="stDataEditor"] tbody tr td:first-child { display:none !important; }
div[data-testid="stDataFrame"] thead tr th:nth-child(2),
div[data-testid="stDataFrame"] tbody tr td:nth-child(2),
div[data-testid="stDataEditor"] thead tr th:nth-child(2),
div[data-testid="stDataEditor"] tbody tr td:nth-child(2) { border-left:none !important; }
[data-testid="stImage"] img { display:block;margin-left:auto;margin-right:auto; }
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

def _to_task_dict(t):
    if isinstance(t, dict): return t
    assignee_email = getattr(getattr(t, "assignee", None), "email", None)
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
    if isinstance(s, dict): return s
    assignee_email = getattr(getattr(s, "assignee", None), "email", None)
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

def centered_logo(path: str = "logo_1.png", width: int = 160) -> None:
    p = Path(path)
    if not p.is_file():
        p = Path(__file__).with_name(path)
    try:
        b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
        html = f'<div style="text-align:center;"><img src="data:image/png;base64,{b64}" style="width:{width}px;max-width:100%;height:auto;" /></div>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        st.image(str(p), width=width)

# ---------- Auth & project gate ----------
def full_screen_login():
    st.markdown("""
    <style>
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display:none!important; }
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
      [data-testid="stSidebar"], [data-testid="baseButton-headerNoPadding"] { display:none!important; }
      .main > div { padding-top: 4vh !important; }
    </style>
    """, unsafe_allow_html=True)
    projects = db.get_projects_for_user(user_email)
    _, col, _ = st.columns([1, 2.6, 1])
    with col:
        centered_logo("logo_1.png", width=140)
        st.markdown("<h2 style='text-align:center;margin-top:8px;'>Choose or Create a Project</h2>", unsafe_allow_html=True)

        if projects:
            # names only
            opt_proj = st.selectbox("Open existing project", options=projects, format_func=lambda p: p.name)
            if st.button("Open project", width='stretch'):
                st.session_state["selected_project_id"] = opt_proj.id
                force_rerun()

        st.markdown("---")
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
                st.session_state["selected_project_id"] = pid
                st.success(f"Project created.")
                force_rerun()

user = st.session_state.get("user")
if not user:
    full_screen_login()
    st.stop()

if not st.session_state.get("selected_project_id"):
    full_screen_project_gate(user["email"])
    st.stop()

def load_logo(path="logo_1.png"):
    return Image.open(path)

with st.sidebar:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 3, 1])
    with c2:
        st.image(load_logo(), width='stretch')
    st.caption(f"Signed in as **{user['email']}**")
    st.markdown("---")

_projects_raw = db.get_projects_for_user(user["email"])
current_project = next((p for p in _projects_raw if p.id == st.session_state.get("selected_project_id")), None)
if not current_project:
    st.session_state["selected_project_id"] = None
    force_rerun()

with st.sidebar:
    st.subheader("Projects")
    # names only
    ids = [p.id for p in _projects_raw]
    idx = max(0, ids.index(current_project.id)) if current_project else 0
    chosen_proj = st.selectbox("Open project", options=_projects_raw, index=idx, format_func=lambda p: p.name)
    if chosen_proj and chosen_proj.id != current_project.id:
        st.session_state["selected_project_id"] = chosen_proj.id
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
            pin_val = st.text_input("Project PIN", type="password", disabled=is_public, key="sb_pin",
                                    help="Members will need this PIN to open the project.")
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
                pid = db.create_project(user["email"], p_name, p_start, p_end, members, is_public=is_public, pin=(pin_val or None))
                st.session_state["selected_project_id"] = pid
                st.success("Project created.")
                force_rerun()

st.title(current_project.name)
st.caption(f"{current_project.start_date} → {current_project.end_date}")

# PIN gate
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
                st.success("Project renamed.")
                force_rerun()
        with colB:
            if st.button("Delete project", type="secondary", key="delete_project_btn"):
                db.delete_project(current_project.id)
                st.success("Project deleted.")
                st.session_state["selected_project_id"] = None
                force_rerun()
    else:
        st.caption("Only the owner can manage this project.")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["Tasks", "Gantt", "Members"])

# ---------- helpers for editors ----------
def _extract_id_set(idx):
    ids = set()
    for i in idx:
        try:
            ids.add(int(i))
        except Exception:
            pass
    return ids

def _has_id_index(df, orig_ids):
    try:
        return len(_extract_id_set(df.index) & orig_ids) > 0
    except Exception:
        return False

# =======================
# Tasks Tab (inline edit)
# =======================
with tab1:
    st.subheader("Tasks")
    if not CAN_WRITE:
        st.info("You have read-only access to this project.")

    raw_tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    task_cols = ["Task", "Status", "Start", "End", "Assignee", "Progress%", "Progress (bar)", "Description"]

    task_records = []
    for t in raw_tasks:
        pct = float(round(t["progress"] or 0, 1))
        task_records.append({
            "Task": t["name"] or "",
            "Status": _norm_status(t["status"]) if t["status"] else "To-Do",
            "Start": t["start_date"],
            "End": t["end_date"],
            "Assignee": t["assignee_email"] or "",
            "Progress%": pct,              # editable number
            "Progress (bar)": pct,         # read-only bar mirror
            "Description": "",
        })

    if task_records:
        df_tasks = pd.DataFrame(task_records, columns=task_cols, index=[t["id"] for t in raw_tasks])
        df_tasks.index.name = ""   # hide the index header so 'id' never appears
    else:
        df_tasks = pd.DataFrame(columns=task_cols)

    edited_tasks = st.data_editor(
        df_tasks.sort_values(by="Start", ascending=True, na_position="last"),
        width='stretch',
        hide_index=True,
        num_rows="dynamic",
        disabled=not CAN_WRITE,
        column_order=task_cols,
        column_config={
            "Task": st.column_config.TextColumn("Task", required=True),
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "Start": st.column_config.DateColumn("Start"),
            "End": st.column_config.DateColumn("End"),
            "Assignee": st.column_config.TextColumn("Assignee"),
            "Progress%": st.column_config.NumberColumn("Progress %", min_value=0, max_value=100, step=1, format="%d%%"),
            "Progress (bar)": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%d%%"),
            "Description": st.column_config.TextColumn("Description", help="Optional notes"),
        },
    )

    if CAN_WRITE and st.button("💾 Save task changes"):
        try:
            orig_ids = {t["id"] for t in raw_tasks if t["id"] is not None}
            edited_df = edited_tasks.copy()

            if _has_id_index(edited_df, orig_ids):
                edited_ids = _extract_id_set(edited_df.index)
                to_delete = orig_ids - edited_ids
            else:
                to_delete = set()

            for del_id in to_delete:
                db.delete_task(int(del_id))

            if _has_id_index(edited_df, orig_ids):
                iterable = edited_df.iterrows()
            else:
                iterable = [(None, row) for _, row in edited_df.iterrows()]

            for maybe_id, row in iterable:
                name = str(row.get("Task", "")).strip()
                if not name:
                    continue
                status = _norm_status(row.get("Status", "To-Do"))
                start = parse_date(row.get("Start"))
                end   = parse_date(row.get("End"))
                assg  = (str(row.get("Assignee", "")).strip() or None)
                try:
                    prog = float(row.get("Progress%", 0) or 0)
                except Exception:
                    prog = 0.0
                prog = float(max(0, min(100, prog)))
                desc  = str(row.get("Description", "")).strip() or None

                db.add_or_update_task(
                    project_id=current_project.id,
                    name=name,
                    status=status if status in STATUS_OPTIONS else "To-Do",
                    start=start,
                    end=end,
                    assignee_email=assg,
                    description=desc,
                    task_id=int(maybe_id) if (maybe_id is not None and int(maybe_id) in orig_ids) else None,
                    progress=prog,
                )

            st.success("Tasks saved.")
            force_rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    st.caption("Import tasks from CSV (Task, Status, Start, End, Assignee, Progress%, Description)")
    up = st.file_uploader(" ", type=["csv"], accept_multiple_files=False, key="task_csv_import", label_visibility="collapsed")
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
                prog = float(max(0, min(100, prog)))
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
                    progress=prog,
                )
                created += 1
            st.success(f"Imported {created} task(s).")
            force_rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.markdown("---")

    # =========================
    # Subtasks inline editor
    # =========================
    st.subheader("Subtasks")

    all_tasks_for_picker = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    if not all_tasks_for_picker:
        st.caption("Create a task first to add subtasks.")
    else:
        # names only in the dropdown
        task_for_sub = st.selectbox(
            "Task",
            options=all_tasks_for_picker,
            format_func=lambda t: (t["name"] or "Untitled Task"),
            key="task_picker_for_subtasks",
        )
        picked_task_id = task_for_sub["id"] if task_for_sub else None

        if picked_task_id:
            raw_subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(picked_task_id)]

            sub_cols = ["Subtask","Status","Start","End","Assignee","Progress%","Progress (bar)"]
            sub_records = []
            for s_ in raw_subs:
                pct = float(round(s_["progress"] or 0, 1))
                sub_records.append({
                    "Subtask": s_["name"] or "",
                    "Status": _norm_status(s_["status"]) if s_["status"] else "To-Do",
                    "Start": s_["start_date"],
                    "End": s_["end_date"],
                    "Assignee": s_["assignee_email"] or "",
                    "Progress%": pct,
                    "Progress (bar)": pct,
                })

            if sub_records:
                df_subs = pd.DataFrame(sub_records, columns=sub_cols, index=[s["id"] for s in raw_subs])
                df_subs.index.name = ""           # hide index header
            else:
                df_subs = pd.DataFrame(columns=sub_cols)

            edited_subs = st.data_editor(
                df_subs.sort_values(by="Start", ascending=True, na_position="last"),
                width='stretch',
                hide_index=True,
                num_rows="dynamic",
                disabled=not CAN_WRITE,
                column_order=sub_cols,
                column_config={
                    "Subtask": st.column_config.TextColumn("Subtask", required=True),
                    "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
                    "Start": st.column_config.DateColumn("Start"),
                    "End": st.column_config.DateColumn("End"),
                    "Assignee": st.column_config.TextColumn("Assignee"),
                    "Progress%": st.column_config.NumberColumn("Progress %", min_value=0, max_value=100, step=1, format="%d%%"),
                    "Progress (bar)": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100, format="%d%%"),
                },
            )

            if CAN_WRITE and st.button("💾 Save subtask changes"):
                try:
                    orig_ids = {s["id"] for s in raw_subs if s["id"] is not None}
                    edited_df = edited_subs.copy()

                    if _has_id_index(edited_df, orig_ids):
                        edited_ids = _extract_id_set(edited_df.index)
                        to_delete = orig_ids - edited_ids
                    else:
                        to_delete = set()

                    for del_id in to_delete:
                        db.delete_subtask(int(del_id))

                    if _has_id_index(edited_df, orig_ids):
                        iterable = edited_df.iterrows()
                    else:
                        iterable = [(None, row) for _, row in edited_df.iterrows()]

                    for maybe_id, row in iterable:
                        name = str(row.get("Subtask", "")).strip()
                        if not name:
                            continue
                        status = _norm_status(row.get("Status", "To-Do"))
                        start = parse_date(row.get("Start"))
                        end   = parse_date(row.get("End"))
                        assg  = (str(row.get("Assignee", "")).strip() or None)
                        try:
                            prog = float(row.get("Progress%", 0) or 0)
                        except Exception:
                            prog = 0.0
                        prog = float(max(0, min(100, prog)))

                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start,
                            end=end,
                            assignee_email=assg,
                            subtask_id=int(maybe_id) if (maybe_id is not None and int(maybe_id) in orig_ids) else None,
                            progress=prog,
                        )

                    st.success("Subtasks saved.")
                    force_rerun()
                except Exception as e:
                    st.error(f"Save failed: {e}")

            st.caption("Import subtasks from CSV (Subtask, Status, Start, End, Assignee, Progress%)")
            up_sub = st.file_uploader(" ", type=["csv"], accept_multiple_files=False,
                                      key=f"sub_csv_import_{picked_task_id}", label_visibility="collapsed")
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
                        prog = float(max(0, min(100, prog)))
                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start,
                            end=end,
                            assignee_email=assg,
                            subtask_id=None,
                            progress=prog,
                        )
                        created += 1
                    st.success(f"Imported {created} subtask(s).")
                    force_rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

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
                "Status": _norm_status(t["status"]),
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
                    "Status": _norm_status(s["status"]),
                    "Assignee": s["assignee_email"],
                    "Progress": round(s["progress"], 1)
                })
    if not rows:
        st.info("Add start/end dates to tasks or subtasks to see them on the Gantt.")
    else:
        df = pd.DataFrame(rows)
        status_colors = {
            "To-Do":       "#9CA3AF",
            "In Progress": "#2563EB",
            "Done":        "#10B981",
        }
        df["Status"] = pd.Categorical(df["Status"], categories=list(status_colors.keys()), ordered=True)
        fig = px.timeline(
            df, x_start="Start", x_end="Finish", y="Item",
            color="Status", hover_data=["Status", "Assignee", "Progress"],
            color_discrete_map=status_colors,
        )
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=30), legend_title_text="Status")
        st.plotly_chart(fig, width='stretch', config={"displaylogo": False, "responsive": True})

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
