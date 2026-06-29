"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create pipeline_runs table
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('branch', sa.String(), nullable=False),
        sa.Column('commit_sha', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('transport_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_runs_run_id'), 'pipeline_runs', ['run_id'], unique=True)

    # 2. Create transport_records table
    op.create_table(
        'transport_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transport_id', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('source_system', sa.String(), nullable=False),
        sa.Column('target_system', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('promoted_by', sa.String(), nullable=False),
        sa.Column('promoted_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('validation_report', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transport_records_transport_id'), 'transport_records', ['transport_id'], unique=True)

    # 3. Create system_health_snapshots table
    op.create_table(
        'system_health_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('cpu_percent', sa.Float(), nullable=False),
        sa.Column('memory_percent', sa.Float(), nullable=False),
        sa.Column('active_users', sa.Integer(), nullable=False),
        sa.Column('avg_response_ms', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_health_snapshots_recorded_at'), 'system_health_snapshots', ['recorded_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_system_health_snapshots_recorded_at'), table_name='system_health_snapshots')
    op.drop_table('system_health_snapshots')
    
    op.drop_index(op.f('ix_transport_records_transport_id'), table_name='transport_records')
    op.drop_table('transport_records')
    
    op.drop_index(op.f('ix_pipeline_runs_run_id'), table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
