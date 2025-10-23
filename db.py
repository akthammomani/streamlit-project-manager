# db.py
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Dict

from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, ForeignKey, Enum, Float, UniqueConstraint, select
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload, Session

DB_URL = "sqlite:///data.db"
engine = create_engine(DB_URL, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)
Base = declarative_base()

TASK_STATUSES = ("Backlog", "In-Progress", "Completed")

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
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User")
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # owner|member
    project = relationship("Project", back_populates="members")
    user = relationship("User")
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(*TASK_STATUSES, name="task_status"), default="Backlog", nullable=False)
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
    status = Column(Enum(*TASK_STATUSES, name="subtask_status"), default="Backlog", nullable=False)
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

# Public helpers the app will call
def login(email: str, name: Optional[str] = None) -> Dict:
    with SessionLocal() as s:
        user = _get_or_create_user(s, email, name)
        return {"id": user.id, "email": user.email, "name": user.name}

def create_project(owner_email: str, name: str, start: date, end: date, member_emails: Optional[List[str]] = None) -> int:
    member_emails = member_emails or []
    with SessionLocal() as s:
        owner = _get_or_create_user(s, owner_email)
        p = Project(name=name, start_date=start, end_date=end, owner_id=owner.id)
        s.add(p)
        s.flush()
        # owner is a member
        s.add(ProjectMember(project_id=p.id, user_id=owner.id, role="owner"))
        for e in member_emails:
            if e and e.strip():
                u = _get_or_create_user(s, e)
                if u.id != owner.id:
                    s.add(ProjectMember(project_id=p.id, user_id=u.id, role="member"))
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

def delete_task(task_id: int) -> None:
    with SessionLocal() as s:
        t = s.get(Task, task_id)
        if t:
            s.delete(t)
            s.commit()

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

def delete_subtask(subtask_id: int) -> None:
    with SessionLocal() as s:
        st = s.get(SubTask, subtask_id)
        if st:
            s.delete(st)
            s.commit()

