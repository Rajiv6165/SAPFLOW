from pydantic import BaseModel, UUID4, field_validator, ValidationError
from typing import Optional, List, Any, Dict
from datetime import datetime
import re


# ─── Pipeline Schemas ──────────────────────────────────────────────────────────


class PipelineRunBase(BaseModel):
    branch: str
    commit_sha: str
    transport_id: Optional[str] = None


class PipelineRunCreate(PipelineRunBase):
    run_id: str
    status: str = "pending"


class PipelineRunResponse(PipelineRunBase):
    id: UUID4
    run_id: str
    status: str
    triggered_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class PipelineStatusResponse(BaseModel):
    current_status: str
    last_runs: List[PipelineRunResponse]


class PipelineMetric(BaseModel):
    date: str
    success: int
    failed: int


class PipelineTriggerRequest(BaseModel):
    branch: str = "main"


class PipelineTriggerResponse(BaseModel):
    message: str
    branch: str


# ─── Transport Schemas ─────────────────────────────────────────────────────────


class TransportPromoteRequest(BaseModel):
    transport_id: str
    source_system: str  # DEV / QA
    target_system: str  # QA / PROD
    promoted_by: str = "system"
    landscape: Optional[str] = "DEFAULT"

    @field_validator("transport_id")
    @classmethod
    def validate_transport_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("transport_id cannot be empty")
        # SAP transport ID format: e.g., DEVK900123, QAK900456
        pattern = r"^[A-Z]{3}K\d{6}$"
        if not re.match(pattern, v):
            raise ValueError("transport_id must match SAP format (e.g., DEVK900123)")
        return v

    @field_validator("target_system")
    @classmethod
    def validate_target_system(cls, v: str) -> str:
        valid_systems = ["DEV", "QA", "PROD"]
        if v not in valid_systems:
            raise ValueError(
                f"target_system must be one of: {', '.join(valid_systems)}"
            )
        if v == "DEV":
            raise ValueError("Cannot promote to DEV (backwards promotion not allowed)")
        return v


class TransportRecordResponse(BaseModel):
    id: UUID4
    transport_id: str
    description: str
    source_system: str
    target_system: str
    status: str
    promoted_by: str
    promoted_at: datetime
    completed_at: Optional[datetime] = None
    validation_report: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TransportHistoryResponse(BaseModel):
    transports: List[TransportRecordResponse]


class TransportValidateRequest(BaseModel):
    transport_id: str


class TransportValidateResponse(BaseModel):
    transport_id: str
    is_valid: bool
    severity: str  # INFO / WARNING / ERROR
    findings: List[str]
    naming_conventions: bool
    dependencies_ok: bool
    report: Dict[str, Any]


# ─── Health Schemas ────────────────────────────────────────────────────────────


class SystemHealthResponse(BaseModel):
    cpu_percent: float
    memory_percent: float
    active_users: int
    avg_response_ms: int
    status: str  # healthy / degraded / down
    recorded_at: Optional[datetime] = None


class SystemHealthHistoryResponse(BaseModel):
    snapshots: List[SystemHealthResponse]


# ─── Alert Schemas ─────────────────────────────────────────────────────────────


class AlertResponse(BaseModel):
    alarm_name: str
    state: str
    reason: Optional[str] = None


class CloudWatchAlarmsResponse(BaseModel):
    alarms: List[AlertResponse]


# ─── Missing Phase 2 Schemas ───────────────────────────────────────────────────


class PipelineMetrics(BaseModel):
    date: str
    success: int
    failed: int


class TransportResponse(TransportRecordResponse):
    pass


class HealthHistoryResponse(BaseModel):
    snapshots: List[SystemHealthResponse]


class WebSocketSummary(BaseModel):
    total_runs_today: int
    success_rate: float
    active_transports: int
    system_status: str


class WebSocketRunDetail(BaseModel):
    id: str
    run_id: str
    branch: str
    commit_sha: str
    status: str
    duration_seconds: Optional[int] = None
    triggered_at: str


class WebSocketPayload(BaseModel):
    type: str = "pipeline_update"
    timestamp: str
    summary: WebSocketSummary
    recent_runs: List[WebSocketRunDetail]
