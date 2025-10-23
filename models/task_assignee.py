# models/task_assignee.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.task import Task
    from models.user import User

class TaskAssignee(SQLModel, table=True):
    __tablename__ = "task_assignees"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id")
    user_id: int = Field(foreign_key="users.id")

    task: "Task" = Relationship(back_populates="assignees")
    user: "User" = Relationship(back_populates="task_assignments")

