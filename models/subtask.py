# models/subtask.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from models.task import Task

class Subtask(SQLModel, table=True):
    __tablename__ = "subtasks"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id")
    title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="Backlog")
    percent_complete: float = Field(default=0.0)
    assignee_email: Optional[str] = None

    task: "Task" = Relationship(back_populates="subtasks")

