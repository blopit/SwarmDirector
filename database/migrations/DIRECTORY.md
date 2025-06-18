---
title: Database Migrations Directory
description: Database schema migrations and version control for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [migrations, schema, database-versioning, alembic]
---

# Database Migrations Directory

## Purpose

The database/migrations directory contains database schema migrations, version control scripts, and migration management tools for SwarmDirector. This directory ensures consistent database schema evolution across different environments and provides a reliable way to upgrade and downgrade database structures.

## Structure

```
database/migrations/
├── README                       # Migration documentation and procedures
├── alembic.ini                  # Alembic configuration file
├── env.py                       # Alembic environment configuration
├── script.py.mako               # Migration script template
├── versions/                    # Migration version files
│   ├── 001_initial_schema.py    # Initial database schema
│   ├── 002_add_agents_table.py  # Agent table creation
│   ├── 003_add_tasks_table.py   # Task table creation
│   ├── 004_add_conversations.py # Conversation tables
│   ├── 005_add_analytics.py     # Analytics tables
│   ├── 006_create_workflow_state_tables.sql # Workflow state tables
│   └── 007_add_cost_tracking.py # Cost tracking tables
├── manual/                      # Manual migration scripts
│   ├── data_cleanup.sql         # Data cleanup scripts
│   ├── index_optimization.sql   # Index optimization
│   └── performance_tuning.sql   # Performance improvements
├── rollback/                    # Rollback scripts
│   ├── rollback_006.sql         # Rollback for version 006
│   ├── rollback_007.sql         # Rollback for version 007
│   └── emergency_rollback.sql   # Emergency rollback procedures
├── seeds/                       # Data seeding scripts
│   ├── initial_agents.sql       # Initial agent configurations
│   ├── sample_tasks.sql         # Sample task data
│   └── test_data.sql            # Test data for development
└── utilities/                   # Migration utilities
    ├── migration_validator.py   # Migration validation tools
    ├── schema_differ.py         # Schema comparison tools
    └── backup_manager.py        # Backup management for migrations
```

## Guidelines

### 1. Organization
- **Version Control**: Use sequential numbering for migration versions
- **Atomic Changes**: Each migration should contain atomic, reversible changes
- **Environment Separation**: Support different migration paths for different environments
- **Rollback Support**: Provide rollback scripts for all migrations

### 2. Naming
- **Migration Files**: Use descriptive names with version prefix (e.g., `001_initial_schema.py`)
- **SQL Files**: Use `.sql` extension for pure SQL migrations
- **Python Files**: Use `.py` extension for Alembic migrations
- **Rollback Files**: Use `rollback_` prefix for rollback scripts

### 3. Implementation
- **Alembic Integration**: Use Alembic for Python-based migrations
- **SQL Support**: Support both Alembic and pure SQL migrations
- **Validation**: Validate migrations before applying
- **Backup Strategy**: Create backups before applying migrations
- **Testing**: Test migrations in development before production

### 4. Documentation
- **Migration Documentation**: Document the purpose and impact of each migration
- **Rollback Procedures**: Document rollback procedures for each migration
- **Schema Changes**: Document all schema changes and their rationale
- **Performance Impact**: Document performance impact of migrations

## Best Practices

### Migration Management
```python
import logging
from alembic import command
from alembic.config import Config
from pathlib import Path

logger = logging.getLogger(__name__)

class MigrationManager:
    def __init__(self, alembic_cfg_path: str):
        self.alembic_cfg = Config(alembic_cfg_path)
        self.migrations_dir = Path(alembic_cfg_path).parent
    
    def create_backup_before_migration(self) -> str:
        """Create database backup before applying migrations."""
        from src.swarm_director.utils.database import DatabaseManager
        
        db_manager = DatabaseManager(self.get_database_url())
        backup_path = db_manager.create_backup("pre_migration_backup.db")
        logger.info(f"Pre-migration backup created: {backup_path}")
        return backup_path
    
    def upgrade_to_head(self) -> bool:
        """Upgrade database to the latest migration."""
        try:
            # Create backup
            self.create_backup_before_migration()
            
            # Apply migrations
            command.upgrade(self.alembic_cfg, "head")
            logger.info("Database upgraded to head")
            return True
        except Exception as e:
            logger.error(f"Migration upgrade failed: {e}")
            return False
    
    def downgrade_to_revision(self, revision: str) -> bool:
        """Downgrade database to specific revision."""
        try:
            # Create backup
            self.create_backup_before_migration()
            
            # Downgrade
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Database downgraded to revision: {revision}")
            return True
        except Exception as e:
            logger.error(f"Migration downgrade failed: {e}")
            return False
    
    def get_current_revision(self) -> str:
        """Get current database revision."""
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import create_engine
        
        engine = create_engine(self.get_database_url())
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()
    
    def validate_migration(self, revision: str) -> bool:
        """Validate a migration before applying."""
        try:
            # Check if migration file exists
            migration_file = self.migrations_dir / "versions" / f"{revision}.py"
            if not migration_file.exists():
                logger.error(f"Migration file not found: {migration_file}")
                return False
            
            # Additional validation logic here
            # - Check for syntax errors
            # - Validate SQL statements
            # - Check for potential data loss
            
            return True
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False
```

### Security
- **Access Control**: Restrict migration execution to authorized users
- **Backup Verification**: Verify backups before applying migrations
- **Rollback Testing**: Test rollback procedures in development
- **Audit Logging**: Log all migration operations

### Performance
- **Migration Timing**: Schedule migrations during low-traffic periods
- **Index Management**: Handle index creation/deletion efficiently
- **Batch Processing**: Use batch processing for large data migrations
- **Progress Monitoring**: Monitor migration progress for long-running operations

### Testing
```python
import pytest
import tempfile
from pathlib import Path
from alembic import command
from alembic.config import Config

@pytest.fixture
def temp_migration_env():
    """Create temporary migration environment for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy migration files to temp directory
        # ... setup migration environment ...
        
        yield temp_path

def test_migration_upgrade_downgrade(temp_migration_env):
    """Test migration upgrade and downgrade."""
    alembic_cfg = Config(str(temp_migration_env / "alembic.ini"))
    
    # Test upgrade
    command.upgrade(alembic_cfg, "head")
    
    # Verify schema changes
    # ... verification logic ...
    
    # Test downgrade
    command.downgrade(alembic_cfg, "base")
    
    # Verify rollback
    # ... verification logic ...

def test_migration_validation():
    """Test migration validation."""
    manager = MigrationManager("alembic.ini")
    
    # Test valid migration
    assert manager.validate_migration("001_initial_schema") is True
    
    # Test invalid migration
    assert manager.validate_migration("999_nonexistent") is False
```

### Error Handling
- **Rollback on Failure**: Automatically rollback on migration failure
- **Error Reporting**: Provide detailed error reporting for migration failures
- **Recovery Procedures**: Document recovery procedures for failed migrations
- **Data Integrity**: Ensure data integrity during migrations

## Examples

### Alembic Migration Script
```python
"""Add cost tracking tables

Revision ID: 007_add_cost_tracking
Revises: 006_create_workflow_state_tables
Create Date: 2025-06-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '007_add_cost_tracking'
down_revision = '006_create_workflow_state_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Add cost tracking tables."""
    # Create cost_tracking table
    op.create_table(
        'cost_tracking',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_cost_tracking_provider', 'cost_tracking', ['provider'])
    op.create_index('idx_cost_tracking_timestamp', 'cost_tracking', ['timestamp'])
    op.create_index('idx_cost_tracking_agent_id', 'cost_tracking', ['agent_id'])
    op.create_index('idx_cost_tracking_task_id', 'cost_tracking', ['task_id'])
    
    # Create cost_budgets table
    op.create_table(
        'cost_budgets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('budget_type', sa.String(50), nullable=False),  # daily, weekly, monthly
        sa.Column('limit_usd', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('current_usage_usd', sa.Numeric(precision=10, scale=2), nullable=False, default=0),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('alert_threshold', sa.Numeric(precision=5, scale=2), nullable=False, default=0.8),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_cost_tracking_agent_id',
        'cost_tracking', 'agents',
        ['agent_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_cost_tracking_task_id',
        'cost_tracking', 'tasks',
        ['task_id'], ['id']
    )

def downgrade():
    """Remove cost tracking tables."""
    # Drop foreign key constraints
    op.drop_constraint('fk_cost_tracking_task_id', 'cost_tracking', type_='foreignkey')
    op.drop_constraint('fk_cost_tracking_agent_id', 'cost_tracking', type_='foreignkey')
    
    # Drop tables
    op.drop_table('cost_budgets')
    op.drop_table('cost_tracking')
```

### Manual SQL Migration
```sql
-- manual/performance_tuning.sql
-- Performance optimization migration

-- Add missing indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks (status, priority);
CREATE INDEX IF NOT EXISTS idx_conversations_agent_id_created_at ON conversations (agent_id, created_at);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs (timestamp);

-- Optimize existing indexes
DROP INDEX IF EXISTS idx_tasks_created_at;
CREATE INDEX idx_tasks_created_at_desc ON tasks (created_at DESC);

-- Add partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_active_agents ON agents (id) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_pending_tasks ON tasks (id, priority) WHERE status = 'pending';

-- Update table statistics
ANALYZE;

-- Log the optimization
INSERT INTO migration_log (migration_name, applied_at, description)
VALUES ('performance_tuning', CURRENT_TIMESTAMP, 'Applied performance optimization indexes');
```

### Migration Validation Script
```python
# utilities/migration_validator.py
import ast
import re
from pathlib import Path
from typing import List, Dict, Any

class MigrationValidator:
    def __init__(self, migrations_dir: str):
        self.migrations_dir = Path(migrations_dir)
    
    def validate_all_migrations(self) -> Dict[str, Any]:
        """Validate all migration files."""
        results = {
            "valid": [],
            "invalid": [],
            "warnings": []
        }
        
        for migration_file in self.migrations_dir.glob("versions/*.py"):
            validation_result = self.validate_migration_file(migration_file)
            
            if validation_result["is_valid"]:
                results["valid"].append(str(migration_file))
            else:
                results["invalid"].append({
                    "file": str(migration_file),
                    "errors": validation_result["errors"]
                })
            
            if validation_result["warnings"]:
                results["warnings"].append({
                    "file": str(migration_file),
                    "warnings": validation_result["warnings"]
                })
        
        return results
    
    def validate_migration_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single migration file."""
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse Python AST
            tree = ast.parse(content)
            
            # Check for required functions
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            if 'upgrade' not in functions:
                result["errors"].append("Missing upgrade() function")
                result["is_valid"] = False
            
            if 'downgrade' not in functions:
                result["errors"].append("Missing downgrade() function")
                result["is_valid"] = False
            
            # Check for dangerous operations
            dangerous_patterns = [
                r'DROP\s+TABLE',
                r'DROP\s+COLUMN',
                r'ALTER\s+TABLE.*DROP'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result["warnings"].append(f"Potentially dangerous operation detected: {pattern}")
            
            # Check for missing indexes on foreign keys
            if 'ForeignKey' in content and 'create_index' not in content:
                result["warnings"].append("Foreign key without corresponding index")
        
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e}")
            result["is_valid"] = False
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
            result["is_valid"] = False
        
        return result
```

## Related Documentation

- [Database Schema](../schemas/README.md) - Database schema documentation
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Alembic migration tool
- [Migration Procedures](../../docs/development/migration_procedures.md) - Migration best practices
- [Database Backup](../data/README.md) - Database backup procedures
- [Schema Design](../../docs/development/schema_design.md) - Database schema design guide
- [Performance Optimization](../../docs/development/database_performance.md) - Database performance tuning
