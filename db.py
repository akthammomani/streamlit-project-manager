# db.py

#============================================================#
#                         Strivio-PM                         #
#============================================================#
# Author      : Aktham Almomani                              #
# Created     : 2025-10-15                                   #
# Version     : V1.0.0                                       #
#------------------------------------------------------------#
# Purpose     : Strivio-PM is a free project manager tool    #
#               with tasks, subtasks, assignees, and Plotly  # 
#               Gantt timelines (SQLite/Supabase powered)    #
#                                                            #
# Change Log  :                                              #
#  - V1.0.0 (2025-10-15): Initial release.                   #
#  - V1.0.1 (planned)   : Enable notifications and many more #
#============================================================#


from __future__ import annotations

import os
from datetime import datetime, date
from typing import Optional, List, Dict

from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, ForeignKey,
    Enum, Float, UniqueConstraint, Boolean, CheckConstraint, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
import hashlib

#DB_URL = "sqlite:///data.db"
#engine = create_engine(DB_URL, future=True, echo=False)
#SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
#Base = declarative_base()

#DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///strivio.db")
#engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
#Base = declarative_base()

# ---- Engine / Session ----
try:
    import streamlit as st
    _secrets = getattr(st, "secrets", {})
except Exception:
    _secrets = {}

DATABASE_URL = (_secrets.get("DATABASE_URL")
                or os.getenv("DATABASE_URL")
                or "sqlite:///strivio.db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

TASK_STATUSES = ("To-Do", "In Progress", "Done")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=False, nullable=False)
    pin_hash  = Column(String, nullable=True)

    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="viewer", nullable=False)  # owner | editor | viewer
    project = relationship("Project", back_populates="members")
    user = relationship("User")
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),
                     CheckConstraint("role IN ('owner','editor','viewer')", name="ck_member_role"),
                     )

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(*TASK_STATUSES, name="task_status"), default="To-Do", nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    progress = Column(Float, default=0.0)  # 0..100

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User")
    subtasks = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")

class SubTask(Base):
    __tablename__ = "subtasks"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(Enum(*TASK_STATUSES, name="subtask_status"), default="To-Do", nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    progress = Column(Float, default=0.0)

    task = relationship("Task", back_populates="subtasks")
    assignee = relationship("User")

def init_db():
    Base.metadata.create_all(engine)

def _get_or_create_user(session, email: str, name: Optional[str] = None) -> User:
    user = session.query(User).filter(User.email == email.strip().lower()).one_or_none()
    if not user:
        user = User(email=email.strip().lower(), name=name)
        session.add(user)
        session.commit()
    return user

# ---- helpers ----
def login(email: str, name: Optional[str] = None) -> Dict:
    with SessionLocal() as s:
        user = _get_or_create_user(s, email, name)
        return {"id": user.id, "email": user.email, "name": user.name}

def create_project(owner_email: str, name: str, start: date, end: date,
                   member_emails: Optional[List[str]] = None,
                   is_public: bool = False, pin: Optional[str] = None) -> int:
    member_emails = member_emails or []
    with SessionLocal() as s:
        owner = _get_or_create_user(s, owner_email)
        p = Project(
            name=name, start_date=start, end_date=end, owner_id=owner.id,
            is_public=is_public, pin_hash=None if is_public else _hash_pin(pin)
        )
        s.add(p); s.flush()
        s.add(ProjectMember(project_id=p.id, user_id=owner.id, role="owner"))
        for e in member_emails:
            if e and e.strip():
                u = _get_or_create_user(s, e)
                if u.id != owner.id:
                    s.add(ProjectMember(project_id=p.id, user_id=u.id, role="viewer"))
        s.commit()
        return p.id

def get_projects_for_user(user_email: str) -> List[Project]:
    with SessionLocal() as s:
        user = _get_or_create_user(s, user_email)
        q = (
            s.query(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .filter(ProjectMember.user_id == user.id)
            .order_by(Project.created_at.desc())
        )
        return q.all()

def get_project(project_id: int) -> Optional[Project]:
    with SessionLocal() as s:
        return s.get(Project, project_id)

def add_or_update_task(project_id: int, name: str, status: str, start: Optional[date], end: Optional[date],
                       assignee_email: Optional[str], description: Optional[str] = None, task_id: Optional[int] = None,
                       progress: float = 0.0) -> int:
    with SessionLocal() as s:
        assignee_id = None
        if assignee_email:
            assignee_id = _get_or_create_user(s, assignee_email).id
        if task_id:
            t = s.get(Task, task_id)
            if not t:
                raise ValueError("Task not found")
            t.name, t.status, t.start_date, t.end_date = name, status, start, end
            t.assignee_id, t.description, t.progress = assignee_id, description, progress
        else:
            t = Task(project_id=project_id, name=name, status=status, start_date=start, end_date=end,
                     assignee_id=assignee_id, description=description, progress=progress)
            s.add(t)
        s.commit()
        return t.id
        
def _hash_pin(pin: str | None) -> str | None:
    if not pin:
        return None
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()

def delete_task(task_id: int) -> None:
    with SessionLocal() as s:
        t = s.get(Task, task_id)
        if t:
            s.delete(t)
            s.commit()

def delete_subtask(subtask_id: int) -> None:
    with SessionLocal() as s:
        st = s.get(SubTask, subtask_id)
        if st:
            s.delete(st)
            s.commit()

def delete_project(project_id: int) -> None:
    with SessionLocal() as s:
        p = s.get(Project, project_id)
        if p:
            s.delete(p)  
            s.commit()

def rename_project(project_id: int, new_name: str) -> None:
    with SessionLocal() as s:
        p = s.get(Project, project_id)
        if p:
            p.name = new_name.strip()
            s.commit()

def update_project_dates(project_id: int, start_date: date, end_date: date) -> bool:
    """
    Update a project's start/end dates. Returns True if updated, False if project not found.
    """
    try:
        with SessionLocal() as s:
            p = s.get(Project, project_id)
            if not p:
                return False
            p.start_date = start_date
            p.end_date = end_date
            s.commit()
            return True
    except Exception:
        return False

def update_project_description(project_id: int, new_description: str) -> bool:
    """
    Update a project's description text. Returns True if updated, False if not found.
    """
    with SessionLocal() as s:
        p = s.get(Project, project_id)
        if not p:
            return False
        p.description = new_description
        s.commit()
        return True


def set_member_role(project_id: int, email: str, role: str = "viewer"):
    with SessionLocal() as s:
        u = _get_or_create_user(s, email)
        m = s.query(ProjectMember).filter_by(project_id=project_id, user_id=u.id).one_or_none()
        if not m:
            m = ProjectMember(project_id=project_id, user_id=u.id, role=role)
            s.add(m)
        else:
            m.role = role
        s.commit()

def get_user_role(project_id: int, email: str) -> str | None:
    with SessionLocal() as s:
        u = _get_or_create_user(s, email)
        m = s.query(ProjectMember).filter_by(project_id=project_id, user_id=u.id).one_or_none()
        return m.role if m else None

def check_project_pin(project_id: int, pin: str | None) -> bool:
    with SessionLocal() as s:
        p = s.get(Project, project_id)
        if not p or p.is_public:
            return True
        return p.pin_hash == _hash_pin(pin or "")

def add_or_update_subtask(task_id: int, name: str, status: str, start: Optional[date], end: Optional[date],
                          assignee_email: Optional[str], subtask_id: Optional[int] = None,
                          progress: float = 0.0) -> int:
    with SessionLocal() as s:
        assignee_id = None
        if assignee_email:
            assignee_id = _get_or_create_user(s, assignee_email).id
        if subtask_id:
            st = s.get(SubTask, subtask_id)
            if not st:
                raise ValueError("Subtask not found")
            st.name, st.status, st.start_date, st.end_date = name, status, start, end
            st.assignee_id, st.progress = assignee_id, progress
        else:
            st = SubTask(task_id=task_id, name=name, status=status, start_date=start, end_date=end,
                         assignee_id=assignee_id, progress=progress)
            s.add(st)
        s.commit()
        return st.id

def get_tasks_for_project(project_id: int):
    """Return plain dicts to avoid detached lazy loads."""
    with SessionLocal() as s:
        rows = (
            s.query(
                Task.id,
                Task.name,
                Task.status,
                Task.start_date,
                Task.end_date,
                Task.progress,
                User.email.label("assignee_email"),
            )
            .outerjoin(User, Task.assignee_id == User.id)
            .filter(Task.project_id == project_id)
            .order_by(Task.id.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "progress": float(r.progress or 0),
                "assignee_email": r.assignee_email,
            }
            for r in rows
        ]

def get_subtasks_for_task(task_id: int):
    """Return plain dicts to avoid detached lazy loads."""
    with SessionLocal() as s:
        rows = (
            s.query(
                SubTask.id,
                SubTask.name,
                SubTask.status,
                SubTask.start_date,
                SubTask.end_date,
                SubTask.progress,
                User.email.label("assignee_email"),
            )
            .outerjoin(User, SubTask.assignee_id == User.id)
            .filter(SubTask.task_id == task_id)
            .order_by(SubTask.id.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "progress": float(r.progress or 0),
                "assignee_email": r.assignee_email,
            }
            for r in rows
        ]



