# ui/import_export_panel.py
import streamlit as st
import pandas as pd

from db import get_session
from models.project import Project
from models.project_member import ProjectMember
from models.task import Task
from models.subtask import Subtask
from models.task_assignee import TaskAssignee
from models.user import User

def render_import_export(project_id: int, current_user_id: int):
    st.subheader("Backup & Restore")

    with get_session() as s:
        project = s.get(Project, project_id)
        export_data = {
            "project": project.dict(),
            "members": [m.dict() for m in s.exec(select(ProjectMember).where(ProjectMember.project_id == project_id)).all()],
            "tasks": [t.dict() for t in s.exec(select(Task).where(Task.project_id == project_id)).all()],
            "subtasks": [st_.dict() for st_ in s.exec(select(Subtask).join(Task).where(Task.project_id == project_id)).all()],
            "assignees": [a.dict() for a in s.exec(select(TaskAssignee).join(Task).where(Task.project_id == project_id)).all()],
        }

    json_str = pd.Series(export_data).to_json()
    st.download_button("⬇️ Export JSON", data=json_str,
                        file_name=f"project_{project_id}.json")

    up = st.file_uploader("Import JSON", type=["json"])
    if up is not None:
        try:
            imported = pd.read_json(up, typ="series").to_dict()
            p = imported["project"]
            with get_session() as s:
                np = Project(name=p.get("name", "Imported Project"),
                             description=p.get("description"),
                             start_date=p.get("start_date"),
                             end_date=p.get("end_date"))
                s.add(np); s.commit(); s.refresh(np)
                id_map = {}
                for t in imported.get("tasks", []):
                    nt = Task(project_id=np.id,
                              title=t.get("title"),
                              status=t.get("status", "Backlog"),
                              start_date=t.get("start_date"),
                              end_date=t.get("end_date"),
                              percent_complete=t.get("percent_complete", 0.0))
                    s.add(nt); s.commit(); s.refresh(nt)
                    id_map[t.get("id")] = nt.id
                for st_ in imported.get("subtasks", []):
                    nst = Subtask(task_id=id_map.get(st_.get("task_id")),
                                  title=st_.get("title"),
                                  start_date=st_.get("start_date"),
                                  end_date=st_.get("end_date"),
                                  status=st_.get("status", "Backlog"),
                                  percent_complete=st_.get("percent_complete", 0.0),
                                  assignee_email=st_.get("assignee_email"))
                    s.add(nst); s.commit()
            # add current user as owner
            with get_session() as s:
                s.add(ProjectMember(project_id=np.id, user_id=current_user_id, role="owner"))
                s.commit()
            st.success("Imported into a new project.")
        except Exception as e:
            st.error(f"Import failed: {e}")
