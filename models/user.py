from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.project_member import ProjectMember
    from models.task_assignee import TaskAssignee

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None

    memberships: List["ProjectMember"] = Relationship(back_populates="user")
    task_assignments: List["TaskAssignee"] = Relationship(back_populates="user")
