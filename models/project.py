# models/project.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
import os
from datetime import date

if TYPE_CHECKING:
    from models.user import User
    from models.task import Task
    from models.project_member import ProjectMember

class Project(SQLModel, table=True):
    __tablename__ = "projects"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    join_code: str = Field(default_factory=lambda: os.urandom(3).hex(), index=True)

    members: List["ProjectMember"] = Relationship(back_populates="project")
    tasks: List["Task"] = Relationship(back_populates="project")

