"""
memory_core/models.py - SQLAlchemy ORM models for AiPi-MemoryCore
Tables: conversations, decisions, open_loops, pods, projects
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime,
    ForeignKey, JSON, Boolean, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

class Base(DeclarativeBase):
    pass

class Conversation(Base):
    __tablename__ = "conversations"
    id                = Column(String, primary_key=True)
    timestamp         = Column(DateTime, default=datetime.utcnow)
    raw_char_count    = Column(Integer, default=0)
    projects_named    = Column(JSON, default=list)
    emotional_markers = Column(JSON, default=list)
    tech_stack        = Column(JSON, default=list)
    pod_id            = Column(String, ForeignKey("pods.id"), nullable=True)
    last_referenced   = Column(DateTime, nullable=True)
    is_stale          = Column(Boolean, default=False)
    decisions  = relationship("Decision",  back_populates="conversation", cascade="all, delete")
    open_loops = relationship("OpenLoop",  back_populates="conversation", cascade="all, delete")

class Decision(Base):
    __tablename__ = "decisions"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    text            = Column(Text)
    is_executed     = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    conversation    = relationship("Conversation", back_populates="decisions")

class OpenLoop(Base):
    __tablename__ = "open_loops"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    text            = Column(Text)
    is_closed       = Column(Boolean, default=False)
    days_open       = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    conversation    = relationship("Conversation", back_populates="open_loops")

class Pod(Base):
    """Phase 2: Semantic cluster of related conversations."""
    __tablename__ = "pods"
    id                = Column(String, primary_key=True)
    label             = Column(String, nullable=True)
    core_technologies = Column(JSON, default=list)
    shared_objective  = Column(Text, nullable=True)
    emotional_driver  = Column(String, nullable=True)
    project_id        = Column(String, ForeignKey("projects.id"), nullable=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    project           = relationship("Project", back_populates="pods")

class Project(Base):
    """Phase 4: Aligned project."""
    __tablename__ = "projects"
    id               = Column(String, primary_key=True)
    name             = Column(String, unique=True)
    category         = Column(String, nullable=True)
    status           = Column(String, default="active")
    is_strategic     = Column(Boolean, default=False)
    last_active      = Column(DateTime, nullable=True)
    completion_ratio = Column(Float, default=0.0)
    created_at       = Column(DateTime, default=datetime.utcnow)
    pods             = relationship("Pod", back_populates="project")

def get_engine(db_path: str = "memory_core/projects.db"):
    return create_engine(f"sqlite:///{db_path}", echo=False)

def init_db(db_path: str = "memory_core/projects.db"):
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    return sessionmaker(bind=engine)()

if __name__ == "__main__":
    init_db()
    print("[models] DB initialised.")
