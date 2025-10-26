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
# Fancy Tabs CSS — put this after st.set_page_config(...)
st.markdown("""
<style>
:root{
  --tab-active:#2563eb;   /* <<< change this to your brand color */
  --tab-bg:#f6f7fb;
  --tab-text:#374151;
}
.stTabs [role="tablist"]{gap:10px;padding:6px 2px 14px 2px;border-bottom:0;}
.stTabs [role="tab"]{
  background:var(--tab-bg); color:var(--tab-text);
  border:1px solid #e5e7eb; border-radius:999px; padding:10px 16px;
  font-weight:600; transition:all .18s; box-shadow:0 1px 0 rgba(17,24,39,.04);
}
.stTabs [role="tab"]:hover{
  background:#fff; color:#111827; border-color:#d1d5db;
  transform:translateY(-1px); box-shadow:0 6px 16px rgba(31,41,55,.06);
}
.stTabs [role="tab"][aria-selected="true"]{
  background:var(--tab-active); color:#fff; border-color:transparent;
  transform:translateY(-1px); box-shadow:0 10px 24px rgba(37,99,235,.25);
}
.stTabs [role="tab"][aria-selected="true"]::after{
  content:""; display:block; height:3px; margin-top:6px; border-radius:999px;
  background:rgba(255,255,255,.85);
}
.stTabs [role="tab"]:focus-visible{outline:2px solid #6366f1; outline-offset:2px;}
@media (max-width:700px){
  .stTabs [role="tab"]{padding:8px 12px;}
  .stTabs [role="tablist"]{gap:6px;}
}
</style>
""", unsafe_allow_html=True)

# Cosmetic
st.markdown("""
<style>
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
            submitted = st.form_submit_button("Sign in / Continue", use_container_width=True)
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
            opt_proj = st.selectbox("Open existing project", options=projects, format_func=lambda p: p.name)
            if st.button("Open project", use_container_width=True):
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
            submit_new = st.form_submit_button("Create project", use_container_width=True)

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
                st.success("Project created.")
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
        st.image(load_logo(), use_container_width=True)
    st.caption(f"Signed in as **{user['email']}**")
    st.markdown("---")

_projects_raw = db.get_projects_for_user(user["email"])
current_project = next((p for p in _projects_raw if p.id == st.session_state.get("selected_project_id")), None)
if not current_project:
    st.session_state["selected_project_id"] = None
    force_rerun()

with st.sidebar:
    st.subheader("Projects")
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
        if st.button("Create project", use_container_width=True, key="sb_create"):
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
        # Name edit
        new_name = st.text_input("Rename project", value=current_project.name, key="rename_proj")

        # Date edits
        c_dates1, c_dates2 = st.columns(2)
        with c_dates1:
            new_start = st.date_input("Start date", value=current_project.start_date, key="proj_start_edit")
        with c_dates2:
            new_end = st.date_input("End date", value=current_project.end_date, key="proj_end_edit")

        cA, cB, cC = st.columns(3)
        with cA:
            if st.button("Save name", key="save_project_name"):
                db.rename_project(current_project.id, new_name)
                st.success("Project renamed.")
                force_rerun()
        with cB:
            if st.button("Save dates", key="save_project_dates"):
                if new_end < new_start:
                    st.warning("End date must be after start date.")
                else:
                    ok = db.update_project_dates(current_project.id, new_start, new_end)
                    if not ok:
                        st.error("Updating dates failed.")
                    else:
                        st.success("Project dates updated.")
                        force_rerun()
        with cC:
            if st.button("Delete project", type="secondary", key="delete_project_btn"):
                db.delete_project(current_project.id)
                st.success("Project deleted.")
                st.session_state["selected_project_id"] = None
                force_rerun()
    else:
        st.caption("Only the owner can manage this project.")
# --- Contacts (sidebar) ---
with st.sidebar:
    st.divider()
    with st.expander("Contacts", expanded=False):
        st.markdown("""
        [![](https://img.shields.io/badge/GitHub-Follow-informational)](https://github.com/akthammomani)
        [![](https://img.shields.io/badge/LinkedIn-Connect-informational)](https://www.linkedin.com/in/akthammomani/)
        [![](https://img.shields.io/badge/Strivio-PM-informational)](https://github.com/akthammomani/strivio-pm)
        [![](https://img.shields.io/badge/-aktham.momani81@gmail.com-c14438?style=flat-square&logo=Gmail&logoColor=white)](mailto:aktham.momani81@gmail.com)
        """, unsafe_allow_html=True)
        st.caption("© Aktham Momani, 2025. All rights reserved.")


# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["Tasks", "Project Analytics", "Members"])

# ---------- row-id mapping helpers (no index-based IDs) ----------
def _build_row_id_map(df_sorted: pd.DataFrame, ids_sorted: list[int]) -> dict[int, int]:
    return {int(i): int(ids_sorted[i]) for i in range(len(ids_sorted)) if ids_sorted[i] is not None}

def _resolve_row_to_id(row_index: int, row_id_map: dict[int, int]) -> int | None:
    return row_id_map.get(int(row_index))

# =======================
# Tasks Tab (inline edit)
# =======================
with tab1:
    st.subheader("Tasks")
    if not CAN_WRITE:
        st.info("You have read-only access to this project.")

    raw_tasks = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]

    task_cols = ["Task", "Status", "Start", "End", "Assignee", "Progress%", "Description"]
    rows, ids_for_rows = [], []
    for t in raw_tasks:
        pct = float(round(t["progress"] or 0, 1))
        rows.append({
            "Task": t["name"] or "",
            "Status": _norm_status(t["status"]) if t["status"] else "To-Do",
            "Start": t["start_date"],
            "End": t["end_date"],
            "Assignee": t["assignee_email"] or "",
            "Progress%": pct,        # editable number only
            "Description": "",
        })
        ids_for_rows.append(t["id"])

    df_tasks = pd.DataFrame(rows, columns=task_cols)
    order = df_tasks.sort_values(by="Start", ascending=True, na_position="last").index.tolist()
    df_tasks_sorted = df_tasks.iloc[order].reset_index(drop=True)
    ids_sorted = [ids_for_rows[i] for i in order]
    task_row_id_map = _build_row_id_map(df_tasks_sorted, ids_sorted)
    st.session_state["task_row_id_map"] = task_row_id_map
    st.session_state["task_orig_ids"] = set([i for i in ids_sorted if i is not None])

    edited_tasks = st.data_editor(
        df_tasks_sorted,
        width="stretch",
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
            "Description": st.column_config.TextColumn("Description", help="Optional notes"),
        },
    )

    if CAN_WRITE and st.button("💾 Save task changes"):
        try:
            edited_df = edited_tasks.copy()
            row_map = st.session_state.get("task_row_id_map", {})
            orig_ids = st.session_state.get("task_orig_ids", set())

            # Detect deletions
            edited_row_indices = set(int(i) for i in edited_df.index)
            all_row_indices = set(row_map.keys())
            removed_rows = all_row_indices - edited_row_indices
            for r in removed_rows:
                del_id = row_map.get(r)
                if del_id in orig_ids:
                    db.delete_task(int(del_id))

            # Upserts
            for row_idx, row in edited_df.iterrows():
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

                maybe_id = _resolve_row_to_id(row_idx, row_map)
                db.add_or_update_task(
                    project_id=current_project.id,
                    name=name,
                    status=status if status in STATUS_OPTIONS else "To-Do",
                    start=start,
                    end=end,
                    assignee_email=assg,
                    description=desc,
                    task_id=int(maybe_id) if (maybe_id in orig_ids) else None,
                    progress=prog,
                )

            st.success("Tasks saved.")
            force_rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

    # -------- Subtasks (RESTORED) --------
    st.markdown("---")
    st.subheader("Subtasks")
    all_tasks_for_picker = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]
    if not all_tasks_for_picker:
        st.caption("Create a task first to add subtasks.")
    else:
        task_for_sub = st.selectbox(
            "Task",
            options=all_tasks_for_picker,
            format_func=lambda t: (t["name"] or "Untitled Task"),
            key="task_picker_for_subtasks",
        )
        picked_task_id = task_for_sub["id"] if task_for_sub else None

        if picked_task_id:
            raw_subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(picked_task_id)]

            sub_cols = ["Subtask","Status","Start","End","Assignee","Progress%"]
            rows_s, ids_for_rows_s = [], []
            for s_ in raw_subs:
                pct = float(round(s_["progress"] or 0, 1))
                rows_s.append({
                    "Subtask": s_["name"] or "",
                    "Status": _norm_status(s_["status"]) if s_["status"] else "To-Do",
                    "Start": s_["start_date"],
                    "End": s_["end_date"],
                    "Assignee": s_["assignee_email"] or "",
                    "Progress%": pct,
                })
                ids_for_rows_s.append(s_["id"])

            df_subs = pd.DataFrame(rows_s, columns=sub_cols)
            order_s = df_subs.sort_values(by="Start", ascending=True, na_position="last").index.tolist()
            df_subs_sorted = df_subs.iloc[order_s].reset_index(drop=True)
            ids_sorted_s = [ids_for_rows_s[i] for i in order_s]
            sub_row_id_map = _build_row_id_map(df_subs_sorted, ids_sorted_s)
            st.session_state[f"sub_row_id_map_{picked_task_id}"] = sub_row_id_map
            st.session_state[f"sub_orig_ids_{picked_task_id}"] = set([i for i in ids_sorted_s if i is not None])

            edited_subs = st.data_editor(
                df_subs_sorted,
                width="stretch",
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
                },
            )

            if CAN_WRITE and st.button("💾 Save subtask changes"):
                try:
                    edited_df = edited_subs.copy()
                    row_map = st.session_state.get(f"sub_row_id_map_{picked_task_id}", {})
                    orig_ids = st.session_state.get(f"sub_orig_ids_{picked_task_id}", set())

                    edited_row_indices = set(int(i) for i in edited_df.index)
                    all_row_indices = set(row_map.keys())
                    removed_rows = all_row_indices - edited_row_indices
                    for r in removed_rows:
                        del_id = row_map.get(r)
                        if del_id in orig_ids:
                            db.delete_subtask(int(del_id))

                    for row_idx, row in edited_df.iterrows():
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

                        maybe_id = _resolve_row_to_id(row_idx, row_map)
                        db.add_or_update_subtask(
                            task_id=picked_task_id,
                            name=name,
                            status=status if status in STATUS_OPTIONS else "To-Do",
                            start=start,
                            end=end,
                            assignee_email=assg,
                            subtask_id=int(maybe_id) if (maybe_id in orig_ids) else None,
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

# =======================
# Project Analytics Tab
# =======================
with tab2:
    st.subheader("Project Analytics")

    # Load tasks
    tasks_raw = [_to_task_dict(t) for t in db.get_tasks_for_project(current_project.id)]

    # Include subtasks in rollups (toggle)
    include_subtasks = st.checkbox("Include subtasks in analytics", value=True)
    if include_subtasks:
        subs_all = []
        for t in tasks_raw:
            subs = [_to_subtask_dict(s) for s in db.get_subtasks_for_task(t["id"])]
            for s in subs:
                subs_all.append({
                    "id": s["id"], "name": s["name"],
                    "status": _norm_status(s["status"]),
                    "start_date": s["start_date"], "end_date": s["end_date"],
                    "assignee_email": s["assignee_email"],
                    "progress": float(s["progress"] or 0),
                    "_type": "Subtask"
                })
        tasks_table = [
            {
                "id": t["id"], "name": t["name"],
                "status": _norm_status(t["status"]),
                "start_date": t["start_date"], "end_date": t["end_date"],
                "assignee_email": t["assignee_email"],
                "progress": float(t["progress"] or 0),
                "_type": "Task"
            } for t in tasks_raw
        ] + subs_all
    else:
        tasks_table = [
            {
                "id": t["id"], "name": t["name"],
                "status": _norm_status(t["status"]),
                "start_date": t["start_date"], "end_date": t["end_date"],
                "assignee_email": t["assignee_email"],
                "progress": float(t["progress"] or 0),
                "_type": "Task"
            } for t in tasks_raw
        ]

    today = date.today()
    dfA = pd.DataFrame(tasks_table)

    # Derived fields
    if not dfA.empty:
        dfA["is_done"] = dfA["status"].fillna("").eq("Done")
        dfA["has_dates"] = dfA["start_date"].notna() & dfA["end_date"].notna()
        dfA["is_overdue"] = dfA["end_date"].notna() & (dfA["end_date"] < today) & (~dfA["is_done"])
    else:
        dfA["is_done"] = []
        dfA["has_dates"] = []
        dfA["is_overdue"] = []

    # Project timeframe KPIs
    p_start = current_project.start_date
    p_end   = current_project.end_date
    total_days = max(0, (p_end - p_start).days + 1)
    elapsed_days = 0
    if today >= p_start:
        elapsed_days = (min(today, p_end) - p_start).days + 1
        elapsed_days = max(0, min(elapsed_days, total_days))
    remaining_days = max(0, total_days - elapsed_days)

    # Work KPIs
    total_items = len(dfA)
    done_items = int(dfA["is_done"].sum()) if total_items else 0
    open_items = total_items - done_items
    overdue_items = int(dfA["is_overdue"].sum()) if total_items else 0
    overall_progress = round(float(dfA["progress"].mean()) if total_items else 0.0, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Days Total", total_days)
    with c2: st.metric("Days Remaining", remaining_days)
    with c3: st.metric("Items (Open/Total)", f"{open_items}/{total_items}")
    with c4: st.metric("Overdue", overdue_items)
    with c5: st.metric("Overall % Complete", f"{overall_progress}%")

    st.markdown("---")

    # ---- Timeline (Gantt)----
    st.markdown("### Timeline - Gantt Chart")
    rowsT = []
    for t in tasks_raw:
        if t["start_date"] and t["end_date"]:
            rowsT.append({
                "Item": f"Task · {t['name']}",
                "Start": t["start_date"],
                "Finish": t["end_date"],
                "Status": _norm_status(t["status"]),
                "Assignee": t["assignee_email"],
                "Progress": round(float(t["progress"] or 0), 1)
            })
        if include_subtasks:
            for s in db.get_subtasks_for_task(t["id"]):
                sdict = _to_subtask_dict(s)
                if sdict["start_date"] and sdict["end_date"]:
                    rowsT.append({
                        "Item": f"Subtask · {sdict['name']}",
                        "Start": sdict["start_date"],
                        "Finish": sdict["end_date"],
                        "Status": _norm_status(sdict["status"]),
                        "Assignee": sdict["assignee_email"],
                        "Progress": round(float(sdict["progress"] or 0), 1)
                    })
    if rowsT:
        dfT = pd.DataFrame(rowsT)
        status_colors = {"To-Do":"#9CA3AF","In Progress":"#2563EB","Done":"#10B981"}
        dfT["Status"] = pd.Categorical(dfT["Status"], categories=list(status_colors.keys()), ordered=True)
        fig_tl = px.timeline(
            dfT, x_start="Start", x_end="Finish", y="Item",
            color="Status", hover_data=["Status","Assignee","Progress"],
            color_discrete_map=status_colors,
        )
        fig_tl.update_layout(margin=dict(l=20,r=20,t=30,b=30), legend_title_text="Status")
        st.plotly_chart(fig_tl, use_container_width=True, config={"displaylogo": False, "responsive": True})
    else:
        st.info("Add start/end dates to items to see them on the timeline.")
    st.markdown("---")
   # ---- Status & Assignee Breakdown (side-by-side, single titles) ----
    st.markdown("### Status & Assignee Breakdown")
    
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("**Distribution by Status**")
        status_order = ["To-Do","In Progress","Done"]
        status_counts = (
            dfA.groupby("status").size().reindex(status_order).fillna(0).astype(int).reset_index(name="count")
            if not dfA.empty else pd.DataFrame({"status": status_order, "count": [0,0,0]})
        )
        fig_status = px.bar(
            status_counts, y="status", x="count", text="count", orientation="h"
        )
        fig_status.update_traces(textposition="outside")
        fig_status.update_layout(margin=dict(l=10, r=10, t=10, b=10), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_status, use_container_width=True, config={"displaylogo": False, "responsive": True})
    
    with col2:
        st.markdown("**Workload by Assignee**")
        assignee_counts = (
            dfA.assign(assignee=dfA["assignee_email"].fillna("Unassigned"))
               .groupby("assignee").size().sort_values(ascending=True).reset_index(name="count")
            if not dfA.empty else pd.DataFrame({"assignee": [], "count": []})
        )
        fig_assignee = px.bar(
            assignee_counts, y="assignee", x="count", text="count", orientation="h"
        )
        fig_assignee.update_traces(textposition="outside")
        fig_assignee.update_layout(margin=dict(l=10, r=10, t=10, b=10), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_assignee, use_container_width=True, config={"displaylogo": False, "responsive": True})

    st.markdown("---")
    # ---- Upcoming deadlines (next 14 days)
    st.markdown("### Upcoming deadlines (next 14 days)")
    #st.caption("Upcoming deadlines (next 14 days)")
    if not dfA.empty:
        soon_mask = dfA["end_date"].notna() & (~dfA["is_done"]) & (dfA["end_date"] >= today) & (dfA["end_date"] <= (today + pd.Timedelta(days=14)))
        upcoming = dfA.loc[soon_mask, ["name","_type","assignee_email","status","end_date","progress"]].sort_values("end_date")
    else:
        upcoming = pd.DataFrame(columns=["name","_type","assignee_email","status","end_date","progress"])
    if not upcoming.empty:
        st.data_editor(
            upcoming.rename(columns={
                "name":"Item", "_type":"Type", "assignee_email":"Assignee",
                "status":"Status", "end_date":"Due", "progress":"Progress%"
            }).reset_index(drop=True),
            width="stretch", hide_index=True, disabled=True,
            column_config={
                "Progress%": st.column_config.NumberColumn("Progress %", min_value=0, max_value=100, step=1, format="%d%%")
            }
        )
    else:
        st.info("No upcoming deadlines in the next 14 days.")

    st.markdown("---")

    # ---- At-Risk / Hygiene
    st.markdown("### At-Risk / Hygiene")
    
    # build frames (safe when dfA is empty)
    missing_dates = dfA.loc[~dfA["has_dates"], ["name","_type","assignee_email","status","progress"]] if not dfA.empty else pd.DataFrame(columns=["name","_type","assignee_email","status","progress"])
    overdue_df    = dfA.loc[dfA["is_overdue"], ["name","_type","assignee_email","status","end_date","progress"]].sort_values("end_date") if not dfA.empty else pd.DataFrame(columns=["name","_type","assignee_email","status","end_date","progress"])
    
    if missing_dates.empty and overdue_df.empty:
        st.success("Nothing is out of order right now.")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Overdue Items", 0)
        with c2:
            st.metric("Items Missing Dates", 0)
    else:
        if not missing_dates.empty:
            st.warning("Items missing start or end dates:")
            st.data_editor(
                missing_dates.rename(columns={"name":"Item","_type":"Type","assignee_email":"Assignee","status":"Status","progress":"Progress%"}).reset_index(drop=True),
                width="stretch", hide_index=True, disabled=True,
                column_config={"Progress%": st.column_config.NumberColumn("Progress %", min_value=0, max_value=100, step=1, format="%d%%")}
            )
        if not overdue_df.empty:
            st.error("Overdue items:")
            st.data_editor(
                overdue_df.rename(columns={"name":"Item","_type":"Type","assignee_email":"Assignee","status":"Status","end_date":"Due","progress":"Progress%"}).reset_index(drop=True),
                width="stretch", hide_index=True, disabled=True,
                column_config={"Progress%": st.column_config.NumberColumn("Progress %", min_value=0, max_value=100, step=1, format="%d%%")}
            )


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
