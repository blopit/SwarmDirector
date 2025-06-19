"""
Migration to add validation and plugin system tables

This migration adds the necessary database tables for the hierarchical
validation system and plugin architecture.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from datetime import datetime


def upgrade():
    """Add validation and plugin system tables"""
    
    # Create validation_records table
    op.create_table(
        'validation_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.Enum('TOOL', 'DEPARTMENT', 'DIRECTOR', name='validationtier'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PASSED', 'FAILED', 'REQUIRES_REVISION', 'ESCALATED', 'ROLLBACK_REQUIRED', name='validationstatus'), nullable=False),
        sa.Column('validator_name', sa.String(length=100), nullable=False),
        sa.Column('validator_version', sa.String(length=20), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('validation_timestamp', sa.DateTime(), nullable=True),
        sa.Column('validation_duration_ms', sa.Integer(), nullable=True),
        sa.Column('rollback_required', sa.Boolean(), nullable=True),
        sa.Column('rollback_reason', sa.Text(), nullable=True),
        sa.Column('rollback_actions', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for validation_records
    op.create_index('idx_validation_task_tier', 'validation_records', ['task_id', 'tier'])
    op.create_index('idx_validation_status_timestamp', 'validation_records', ['status', 'validation_timestamp'])
    op.create_index('idx_validation_agent_tier', 'validation_records', ['agent_id', 'tier'])
    op.create_index('idx_validation_rollback', 'validation_records', ['rollback_required'])
    
    # Create quality_gate_configs table
    op.create_table(
        'quality_gate_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('tier', sa.Enum('TOOL', 'DEPARTMENT', 'DIRECTOR', name='validationtier'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_data', sa.JSON(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create rollback_records table
    op.create_table(
        'rollback_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('validation_record_id', sa.Integer(), nullable=True),
        sa.Column('failure_tier', sa.String(length=50), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('steps_executed', sa.JSON(), nullable=True),
        sa.Column('execution_log', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['validation_record_id'], ['validation_records.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for rollback_records
    op.create_index('idx_rollback_task_executed', 'rollback_records', ['task_id', 'executed_at'])
    op.create_index('idx_rollback_success', 'rollback_records', ['success'])
    
    # Create plugin_records table
    op.create_table(
        'plugin_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('plugin_type', sa.Enum('AGENT', 'TOOL', 'VALIDATOR', 'INTEGRATION', 'WORKFLOW', 'EXTENSION', name='plugintype'), nullable=False),
        sa.Column('status', sa.Enum('AVAILABLE', 'INSTALLED', 'ACTIVE', 'DISABLED', 'ERROR', 'UPDATING', name='pluginstatus'), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('dependencies', sa.JSON(), nullable=True),
        sa.Column('entry_point', sa.String(length=200), nullable=True),
        sa.Column('config_schema', sa.JSON(), nullable=True),
        sa.Column('install_path', sa.String(length=500), nullable=True),
        sa.Column('installed_at', sa.DateTime(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('min_swarm_director_version', sa.String(length=20), nullable=True),
        sa.Column('max_swarm_director_version', sa.String(length=20), nullable=True),
        sa.Column('python_version', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('license', sa.String(length=50), nullable=True),
        sa.Column('homepage', sa.String(length=200), nullable=True),
        sa.Column('repository', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for plugin_records
    op.create_index('idx_plugin_type_status', 'plugin_records', ['plugin_type', 'status'])
    op.create_index('idx_plugin_name_version', 'plugin_records', ['name', 'version'])
    op.create_index('idx_plugin_installed_at', 'plugin_records', ['installed_at'])
    
    # Create plugin_installations table
    op.create_table(
        'plugin_installations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('plugin_record_id', sa.Integer(), nullable=False),
        sa.Column('installation_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('dependencies_installed', sa.JSON(), nullable=True),
        sa.Column('installation_log', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['plugin_record_id'], ['plugin_records.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for plugin_installations
    op.create_index('idx_installation_plugin_started', 'plugin_installations', ['plugin_record_id', 'started_at'])
    op.create_index('idx_installation_status', 'plugin_installations', ['status'])
    
    # Create capability_gaps table
    op.create_table(
        'capability_gaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('capability_name', sa.String(length=100), nullable=False),
        sa.Column('capability_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('effort_to_resolve', sa.String(length=20), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_method', sa.String(length=50), nullable=True),
        sa.Column('suggested_plugins', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for capability_gaps
    op.create_index('idx_gap_task_capability', 'capability_gaps', ['task_id', 'capability_name'])
    op.create_index('idx_gap_severity_resolved', 'capability_gaps', ['severity', 'resolved'])
    op.create_index('idx_gap_discovered_at', 'capability_gaps', ['created_at'])
    
    # Create agent_templates table
    op.create_table(
        'agent_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('base_class', sa.String(length=200), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('required_plugins', sa.JSON(), nullable=True),
        sa.Column('config_schema', sa.JSON(), nullable=True),
        sa.Column('initialization_params', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for agent_templates
    op.create_index('idx_template_name_version', 'agent_templates', ['name', 'version'])
    op.create_index('idx_template_agent_type', 'agent_templates', ['agent_type'])
    op.create_index('idx_template_active', 'agent_templates', ['is_active'])
    
    # Add validation-related columns to existing tasks table
    op.add_column('tasks', sa.Column('validation_status', sa.String(length=50), nullable=True))
    op.add_column('tasks', sa.Column('validation_score', sa.Float(), nullable=True))
    op.add_column('tasks', sa.Column('validation_tier', sa.String(length=20), nullable=True))
    op.add_column('tasks', sa.Column('plugin_requirements', sa.JSON(), nullable=True))
    op.add_column('tasks', sa.Column('capability_gaps', sa.JSON(), nullable=True))
    
    # Add plugin-related columns to existing agents table
    op.add_column('agents', sa.Column('plugin_source', sa.String(length=100), nullable=True))
    op.add_column('agents', sa.Column('template_id', sa.Integer(), nullable=True))
    op.add_column('agents', sa.Column('validation_tier', sa.String(length=20), nullable=True))
    
    # Create foreign key for template_id
    op.create_foreign_key('fk_agent_template', 'agents', 'agent_templates', ['template_id'], ['id'])


def downgrade():
    """Remove validation and plugin system tables"""
    
    # Remove added columns from existing tables
    op.drop_constraint('fk_agent_template', 'agents', type_='foreignkey')
    op.drop_column('agents', 'validation_tier')
    op.drop_column('agents', 'template_id')
    op.drop_column('agents', 'plugin_source')
    
    op.drop_column('tasks', 'capability_gaps')
    op.drop_column('tasks', 'plugin_requirements')
    op.drop_column('tasks', 'validation_tier')
    op.drop_column('tasks', 'validation_score')
    op.drop_column('tasks', 'validation_status')
    
    # Drop tables in reverse order
    op.drop_table('agent_templates')
    op.drop_table('capability_gaps')
    op.drop_table('plugin_installations')
    op.drop_table('plugin_records')
    op.drop_table('rollback_records')
    op.drop_table('quality_gate_configs')
    op.drop_table('validation_records')
    
    # Drop custom enums (if using PostgreSQL)
    # For SQLite, enums are stored as strings, so no need to drop them
