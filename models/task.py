# models/task.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from models.project import Project
    from models.subtask import Subtask
    from models.task_assignee import TaskAssignee

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    title: str
    status: str = Field(default="Backlog")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    percent_complete: float = Field(default=0.0)

    project: "Project" = Relationship(back_populates="tasks")
    subtasks: List["Subtask"] = Relationship(back_populates="task")
    assignees: List["TaskAssignee"] = Relationship(back_populates="task")
