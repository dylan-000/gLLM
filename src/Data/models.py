import enum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    Index,
    func,
    text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from .database import Base

'''
Be very careful when modifying the schema. Chainlit's backend expects some columns and their respective names to be present
when it interacts with the database. So, basically don't rename anything to something else.
'''

class StepType(enum.Enum):
    assistant_message = "assistant_message"
    embedding = "embedding"
    llm = "llm"
    retrieval = "retrieval"
    rerank = "rerank"
    run = "run"
    system_message = "system_message"
    tool = "tool"
    undefined = "undefined"
    user_message = "user_message"

class UserRole(enum.Enum):
    admin = "admin"
    fine_tuner = "fine_tuner"
    normal = "normal"
    unauthorized = "unauthorized"

class User(Base):
    __tablename__ = "User"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False) # 'metadata' is reserved in SQLAlchemy Base
    identifier = Column(String, nullable=False, unique=True) # Treat this as the username. Chainlit needs this and this must not be modified.
    
    password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole, name="UserRole"), nullable=False)
    
    threads = relationship("Thread", back_populates="user")

    __table_args__ = (
        Index("ix_User_identifier", "identifier"),
        Index("ix_User_role", "role")
    )


class Thread(Base):
    __tablename__ = "Thread"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deletedAt = Column(DateTime(timezone=True), nullable=True)
    name = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False)
    tags = Column(ARRAY(String), server_default=text("ARRAY[]::text[]"), nullable=False)
    userId = Column(UUID(as_uuid=True), ForeignKey("User.id"), nullable=True)

    user = relationship("User", back_populates="threads")
    elements = relationship("Element", back_populates="thread")
    steps = relationship("Step", back_populates="thread")

    __table_args__ = (
        Index("ix_Thread_createdAt", "createdAt"),
        Index("ix_Thread_name", "name"),
    )


class Step(Base):
    __tablename__ = "Step"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    parentId = Column(UUID(as_uuid=True), ForeignKey("Step.id", ondelete="CASCADE"), nullable=True)
    threadId = Column(UUID(as_uuid=True), ForeignKey("Thread.id", ondelete="CASCADE"), nullable=True)
    
    input = Column(String, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False)
    name = Column(String, nullable=True)
    output = Column(String, nullable=True)
    type = Column(SAEnum(StepType, name="StepType"), nullable=False)
    showInput = Column(String, server_default="json", nullable=True)
    isError = Column(Boolean, server_default="false", nullable=True)
    
    startTime = Column(DateTime(timezone=True), nullable=False)
    endTime = Column(DateTime(timezone=True), nullable=False)

    elements = relationship("Element", back_populates="step")
    feedback = relationship("Feedback", back_populates="step")
    thread = relationship("Thread", back_populates="steps")
    
    parent = relationship("Step", remote_side=[id], back_populates="children")
    children = relationship("Step", back_populates="parent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_Step_createdAt", "createdAt"),
        Index("ix_Step_endTime", "endTime"),
        Index("ix_Step_parentId", "parentId"),
        Index("ix_Step_startTime", "startTime"),
        Index("ix_Step_threadId", "threadId"),
        Index("ix_Step_type", "type"),
        Index("ix_Step_name", "name"),
        Index("ix_Step_threadId_startTime_endTime", "threadId", "startTime", "endTime"),
    )


class Element(Base):
    __tablename__ = "Element"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    threadId = Column(UUID(as_uuid=True), ForeignKey("Thread.id", ondelete="CASCADE"), nullable=True)
    stepId = Column(UUID(as_uuid=True), ForeignKey("Step.id", ondelete="CASCADE"), nullable=False)
    
    metadata_ = Column("metadata", JSONB, nullable=False)
    mime = Column(String, nullable=True)
    name = Column(String, nullable=False)
    objectKey = Column(String, nullable=True)
    url = Column(String, nullable=True)
    
    chainlitKey = Column(String, nullable=True)
    display = Column(String, nullable=True)
    size = Column(String, nullable=True)
    language = Column(String, nullable=True)
    page = Column(Integer, nullable=True)
    props = Column(JSONB, nullable=True)

    step = relationship("Step", back_populates="elements")
    thread = relationship("Thread", back_populates="elements")

    __table_args__ = (
        Index("ix_Element_stepId", "stepId"),
        Index("ix_Element_threadId", "threadId"),
    )


class Feedback(Base):
    __tablename__ = "Feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    stepId = Column(UUID(as_uuid=True), ForeignKey("Step.id"), nullable=True)
    
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    comment = Column(String, nullable=True)

    step = relationship("Step", back_populates="feedback")

    __table_args__ = (
        Index("ix_Feedback_createdAt", "createdAt"),
        Index("ix_Feedback_name", "name"),
        Index("ix_Feedback_stepId", "stepId"),
        Index("ix_Feedback_value", "value"),
        Index("ix_Feedback_name_value", "name", "value"),
    )