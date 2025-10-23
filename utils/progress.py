# utils/progress.py
from sqlmodel import select
from db import get_session
from models.task import Task
from models.subtask import Subtask

def compute_task_progress(task: Task, session) -> float:
    subs = session.exec(select(Subtask).where(Subtask.task_id == task.id)).all()
    if subs:
        vals = [sub.percent_complete for sub in subs]
        return float(sum(vals) / len(vals)) if vals else 0.0
    return float(task.percent_complete)

def compute_project_progress(project_id: int) -> float:
    with get_session() as s:
        tasks = s.exec(select(Task).where(Task.project_id == project_id)).all()
        if not tasks:
            return 0.0
        vals = [compute_task_progress(t, s) for t in tasks]
        return float(sum(vals) / len(vals))
