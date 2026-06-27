from sqlalchemy import Column, String, DateTime, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String, unique=True, nullable=False, index=True)
    branch = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending / running / success / failed
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    transport_id = Column(String, nullable=True)


class TransportRecord(Base):
    __tablename__ = "transport_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transport_id = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=False)
    source_system = Column(String, nullable=False)  # DEV / QA / PROD
    target_system = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending / in_progress / success / failed
    promoted_by = Column(String, nullable=False)
    promoted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    validation_report = Column(JSON, nullable=True)


class SystemHealthSnapshot(Base):
    __tablename__ = "system_health_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    active_users = Column(Integer, nullable=False)
    avg_response_ms = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # healthy / degraded / down
