# ui/tasks_panel.py
import streamlit as st
from datetime import date

from db import get_session
from models.task import Task
from models.task_assignee import TaskAssignee
from models.subtask import Subtask
from models.user import User

STATUS_ORDER = ["Backlog", "In Progress", "Blocked", "Done"]

def render_tasks_panel(project_id: int, current_user_id: int, current_user_email: str):
    st.subheader("Tasks")
    if member_role(current_user_id, project_id) == "viewer":
        st.info("View‑only access. Ask an owner to upgrade your role to edit.")
    else:
        with st.form("new_task", clear_on_submit=True):
            t_title = st.text_input("Task title")
            t_status = st.selectbox("Status", STATUS_ORDER, index=0)
            t_start = st.date_input("Start", value=date.today(), key="t_start")
            t_end = st.date_input("End", value=date.today(), key="t_end")
            t_pct = st.slider("Percent complete", 0, 100, 0)
            notify = st.checkbox("Notify assignees on save", value=False)
            submit_task = st.form_submit_button("Add task")
        if submit_task and t_title:
            with get_session() as s:
                t = Task(project_id=project_id, title=t_title,
                         status=t_status, start_date=t_start,
                         end_date=t_end, percent_complete=float(t_pct))
                s.add(t); s.commit(); s.refresh(t)
            if notify and current_user_email:
                send_email(current_user_email,
                           f"Task created: {t_title}",
                           f"<p>Task <b>{t_title}</b> has been created.</p>")
            st.success("Task added")

    with get_session() as s:
        tasks = s.exec(select(Task).where(Task.project_id == project_id)).all()
    for t in tasks:
        with st.expander(f"🧩 {t.title} — {t.status}"):
            c1, c2, c3, c4 = st.columns(4)
            new_status = c1.selectbox("Status", STATUS_ORDER,
                                     index=STATUS_ORDER.index(t.status), key=f"st_{t.id}")
            new_start = c2.date_input("Start", value=t.start_date or date.today(),
                                     key=f"sd_{t.id}")
            new_end = c3.date_input("End", value=t.end_date or date.today(),
                                   key=f"ed_{t.id}")
            new_pct = c4.slider("%", 0, 100, int(t.percent_complete),
                               key=f"pc_{t.id}")

            st.markdown("**Assignees (task‑level)**")
            with get_session() as s2:
                assn = s2.exec(select(TaskAssignee).where(TaskAssignee.task_id == t.id)).all()
                current_assignees = [s2.get(User, a.user_id).email for a in assn]
            st.write(", ".join(current_assignees) or "—")
            new_email = st.text_input("Add assignee by email", key=f"ae_{t.id}")
            add_assignee = st.button("Add assignee", key=f"ab_{t.id}")
            if add_assignee and new_email:
                u = upsert_user(new_email)
                with get_session() as s2:
                    s2.add(TaskAssignee(task_id=t.id, user_id=u.id))
                    s2.commit()
                send_email(new_email,
                           f"Assigned to task: {t.title}",
                           f"<p>You were assigned to <b>{t.title}</b>.</p>")
                st.success(f"Added {new_email}")

            if st.button("Save task", key=f"sv_{t.id}"):
                with get_session() as s2:
                    tt = s2.get(Task, t.id)
                    tt.status = new_status
                    tt.start_date = new_start
                    tt.end_date = new_end
                    tt.percent_complete = float(new_pct)
                    s2.add(tt); s2.commit()
                st.success("Task saved")

            st.markdown("---")
            st.markdown("**Subtasks**")
            with st.form(f"new_subtask_{t.id}", clear_on_submit=True):
                st_title = st.text_input("Title", key=f"stitle_{t.id}")
                st_start = st.date_input("Start", value=t.start_date or date.today(),
                                         key=f"sst_start_{t.id}")
                st_end = st.date_input("End", value=t.end_date or date.today(),
                                       key=f"sst_end_{t.id}")
                st_status = st.selectbox("Status", STATUS_ORDER, index=0,
                                         key=f"sst_status_{t.id}")
                st_pct = st.slider("% complete", 0, 100, 0, key=f"spc_{t.id}")
                st_assignee = st.text_input("Assignee email (optional)",
                                            key=f"sae_{t.id}")
                sub_submit = st.form_submit_button("Add subtask")
            if sub_submit and st_title:
                with get_session() as s3:
                    st_obj = Subtask(task_id=t.id, title=st_title,
                                     start_date=st_start, end_date=st_end,
                                     status=st_status, percent_complete=float(st_pct),
                                     assignee_email=(st_assignee or None))
                    s3.add(st_obj); s3.commit()
                if st_assignee:
                    send_email(st_assignee,
                               f"Assigned subtask: {st_title}",
                               f"<p>You were assigned to subtask <b>{st_title}</b>.</p>")
                st.success("Subtask added")

            with get_session() as s4:
                subs = s4.exec(select(Subtask).where(Subtask.task_id == t.id)).all()
            if subs:
                for sst in subs:
                    sc1, sc2, sc3, sc4, sc5 = st.columns([2,1,1,1,1])
                    sc1.text_input("Title", value=sst.title, key=f"ti_{sst.id}")
                    sc2.date_input("Start", value=sst.start_date, key=f"ts_{sst.id}")
                    sc3.date_input("End", value=sst.end_date, key=f"te_{sst.id}")
                    sc4.selectbox("Status", STATUS_ORDER,
                                  index=STATUS_ORDER.index(sst.status), key=f"tsb_{sst.id}")
                    sc5.slider("%", 0, 100, int(sst.percent_complete), key=f"tpc_{sst.id}")
                    sd1, sd2 = st.columns([1,1])
                    sd1.text_input("Assignee", value=sst.assignee_email or "", key=f"tae_{sst.id}")
                    if sd2.button("Save", key=f"tsave_{sst.id}"):
                        with get_session() as s5:
                            row = s5.get(Subtask, sst.id)
                            row.title = st.session_state[f"ti_{sst.id}"]
                            row.start_date = st.session_state[f"ts_{sst.id}"]
                            row.end_date = st.session_state[f"te_{sst.id}"]
                            row.status = st.session_state[f"tsb_{sst.id}"]
                            row.percent_complete = float(st.session_state[f"tpc_{sst.id}"])
                            row.assignee_email = (st.session_state[f"tae_{sst.id}"] or None)
                            s5.add(row); s5.commit()
                        st.success("Saved")
