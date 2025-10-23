# models/task_assignee.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from models.task import Task
from models.user import User

class TaskAssignee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    user_id: int = Field(foreign_key="user.id")

    task: Task = Relationship(back_populates="assignees")
    user: User = Relationship(back_populates="task_assignments")
