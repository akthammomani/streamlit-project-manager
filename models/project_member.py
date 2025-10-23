# models/project_member.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.project import Project
    from models.user import User

class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)

    # ✅ Foreign keys must explicitly link to parent tables
    project_id: int = Field(foreign_key="projects.id")
    user_id: int = Field(foreign_key="users.id")
    role: str = Field(default="member")

    # ✅ Proper relationships
    project: "Project" = Relationship(back_populates="members")
    user: "User" = Relationship(back_populates="memberships")
