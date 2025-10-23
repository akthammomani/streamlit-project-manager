# models/project_member.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from models.project import Project
from models.user import User

class ProjectMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    user_id: int = Field(foreign_key="user.id")
    role: str = Field(default="member")

    project: Project = Relationship(back_populates="members")
    user: User = Relationship(back_populates="memberships")
