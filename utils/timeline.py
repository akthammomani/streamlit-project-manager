# utils/timeline.py
import pandas as pd
from sqlmodel import select
from db import get_session
from models.task import Task
from models.subtask import Subtask

def timeline_df_for_project(project_id: int) -> pd.DataFrame:
    with get_session() as s:
        tasks = s.exec(select(Task).where(Task.project_id == project_id)).all()
        rows = []
        for t in tasks:
            rows.append({
                "Item": f"Task: {t.title}",
                "Start": t.start_date,
                "Finish": t.end_date,
                "Status": t.status,
                "Type": "Task"
            })
            subs = s.exec(select(Subtask).where(Subtask.task_id == t.id)).all()
            for st_ in subs:
                rows.append({
                    "Item": f"  ↳ {st_.title}",
                    "Start": st_.start_date,
                    "Finish": st_.end_date,
                    "Status": st_.status,
                    "Type": "Subtask"
                })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["Start", "Finish"], how="any")
        return df
