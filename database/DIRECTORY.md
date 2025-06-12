# Database Directory

## Purpose
Contains database-related files for the SwarmDirector application, including schema definitions, migration scripts, seed data, and database backups. This directory manages all aspects of data persistence for the hierarchical AI agent management system using SQLAlchemy ORM with support for both SQLite (development) and PostgreSQL (production).

## Structure
```
database/
├── data/                        # Database files and backups
│   ├── swarm_director_dev.db    # SQLite development database
│   ├── swarm_director_dev_backup.db # Development database backup
│   └── backups/                 # Automated database backups
├── migrations/                  # Alembic migration files
│   ├── README                   # Migration documentation
│   ├── alembic.ini              # Alembic configuration
│   ├── env.py                   # Migration environment setup
│   ├── script.py.mako           # Migration script template
│   └── versions/                # Migration version files
│       ├── 001_initial_schema.py # Initial database schema
│       ├── 002_add_agent_hierarchy.py # Agent hierarchy support
│       └── 003_add_conversation_tracking.py # Conversation tracking
├── schemas/                     # Database schema definitions
│   ├── database_schema.sql      # Complete schema definition
│   ├── database_schema_documented.sql # Documented schema with comments
│   └── schema.sql               # Legacy schema file
└── seeds/                       # Seed data for development and testing
    ├── initial_agents.sql       # Initial agent configurations
    ├── sample_tasks.sql         # Sample task data
    └── test_data.sql            # Test data for development
```

## Guidelines

### 1. Organization
- **Environment Separation**: Keep development and production database files separate
- **Migration Management**: Use Alembic for all schema changes and versioning
- **Backup Strategy**: Implement regular backup procedures for all environments
- **Schema Documentation**: Maintain comprehensive schema documentation
- **Seed Data Management**: Organize seed data by purpose and environment

### 2. Naming
- **Migration Files**: Use descriptive names with version numbers (e.g., `001_initial_schema.py`)
- **Database Files**: Include environment in filename (e.g., `swarm_director_dev.db`)
- **Schema Files**: Use clear, descriptive names indicating purpose
- **Backup Files**: Include timestamp in backup filenames
- **Seed Files**: Use descriptive names indicating data purpose

### 3. Implementation
- **Migration Scripts**: Write reversible migrations with proper up/down methods
- **Schema Validation**: Validate schema changes before applying to production
- **Data Integrity**: Ensure referential integrity and proper constraints
- **Performance**: Create appropriate indexes for query performance
- **Security**: Use parameterized queries and proper access controls

### 4. Documentation
- **Schema Documentation**: Document all tables, columns, and relationships
- **Migration Documentation**: Document the purpose and impact of each migration
- **Backup Procedures**: Document backup and restore procedures
- **Performance Guidelines**: Document query optimization and indexing strategies

## Best Practices

### 1. Error Handling
- **Migration Rollback**: Ensure all migrations can be safely rolled back
- **Data Validation**: Validate data integrity before and after migrations
- **Error Recovery**: Implement recovery procedures for failed migrations
- **Backup Verification**: Verify backup integrity regularly
- **Constraint Handling**: Handle constraint violations gracefully

### 2. Security
- **Access Control**: Implement proper database access controls
- **Credential Management**: Secure database credentials and connection strings
- **Data Encryption**: Encrypt sensitive data at rest and in transit
- **Audit Logging**: Log all database schema changes and administrative actions
- **Backup Security**: Secure database backups with encryption

### 3. Performance
- **Index Strategy**: Create appropriate indexes for query performance
- **Query Optimization**: Optimize slow queries and monitor performance
- **Connection Pooling**: Configure appropriate connection pooling
- **Partitioning**: Use table partitioning for large datasets
- **Monitoring**: Monitor database performance and resource usage

### 4. Testing
- **Migration Testing**: Test all migrations in staging environment first
- **Data Integrity Testing**: Test referential integrity and constraints
- **Performance Testing**: Test query performance with realistic data volumes
- **Backup Testing**: Regularly test backup and restore procedures
- **Schema Validation**: Validate schema changes against application code

### 5. Documentation
- **Schema Documentation**: Maintain up-to-date schema documentation
- **Migration Log**: Keep detailed log of all schema changes
- **Backup Documentation**: Document backup and restore procedures
- **Performance Documentation**: Document query optimization strategies

## Example

### Complete Migration Script

```python
"""
Add conversation tracking support

Revision ID: 003_add_conversation_tracking
Revises: 002_add_agent_hierarchy
Create Date: 2023-12-01 10:00:00.000000

This migration adds comprehensive conversation tracking capabilities
to support agent communication and workflow coordination.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import enum

# revision identifiers
revision = '003_add_conversation_tracking'
down_revision = '002_add_agent_hierarchy'
branch_labels = None
depends_on = None

class ConversationStatus(enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class MessageType(enum.Enum):
    """Message type enumeration"""
    TEXT = "text"
    SYSTEM = "system"
    ERROR = "error"
    NOTIFICATION = "notification"

def upgrade():
    """
    Add conversation tracking tables and relationships
    """
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum(ConversationStatus), nullable=False, default=ConversationStatus.ACTIVE),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('created_by_agent_id', sa.Integer(), nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=False, default=0),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_agent_id'], ['agents.id'], ondelete='SET NULL')
    )
    
    # Create indexes for conversations
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_task_id', 'conversations', ['task_id'])
    op.create_index('idx_conversations_created_by', 'conversations', ['created_by_agent_id'])
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'])
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender_agent_id', sa.Integer(), nullable=True),
        sa.Column('message_type', sa.Enum(MessageType), nullable=False, default=MessageType.TEXT),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('parent_message_id', sa.Integer(), nullable=True),
        sa.Column('thread_id', sa.String(50), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, default=False),
        sa.Column('edit_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_message_id'], ['messages.id'], ondelete='SET NULL')
    )
    
    # Create indexes for messages
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_sender_agent_id', 'messages', ['sender_agent_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_thread_id', 'messages', ['thread_id'])
    op.create_index('idx_messages_parent_id', 'messages', ['parent_message_id'])
    
    # Create conversation_participants table for many-to-many relationship
    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='participant'),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_read_message_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['last_read_message_id'], ['messages.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('conversation_id', 'agent_id', name='uq_conversation_agent')
    )
    
    # Create indexes for conversation_participants
    op.create_index('idx_conv_participants_conversation', 'conversation_participants', ['conversation_id'])
    op.create_index('idx_conv_participants_agent', 'conversation_participants', ['agent_id'])
    op.create_index('idx_conv_participants_active', 'conversation_participants', ['is_active'])
    
    # Add conversation tracking columns to existing tables
    op.add_column('tasks', sa.Column('conversation_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_tasks_conversation_id',
        'tasks', 'conversations',
        ['conversation_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_tasks_conversation_id', 'tasks', ['conversation_id'])
    
    # Add conversation analytics columns to agents
    op.add_column('agents', sa.Column('total_conversations', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('total_messages_sent', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('average_response_time', sa.Float(), nullable=True))
    op.add_column('agents', sa.Column('last_conversation_at', sa.DateTime(), nullable=True))

def downgrade():
    """
    Remove conversation tracking tables and relationships
    """
    # Remove added columns from existing tables
    op.drop_index('idx_tasks_conversation_id', 'tasks')
    op.drop_constraint('fk_tasks_conversation_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'conversation_id')
    
    op.drop_column('agents', 'total_conversations')
    op.drop_column('agents', 'total_messages_sent')
    op.drop_column('agents', 'average_response_time')
    op.drop_column('agents', 'last_conversation_at')
    
    # Drop conversation_participants table
    op.drop_index('idx_conv_participants_conversation', 'conversation_participants')
    op.drop_index('idx_conv_participants_agent', 'conversation_participants')
    op.drop_index('idx_conv_participants_active', 'conversation_participants')
    op.drop_table('conversation_participants')
    
    # Drop messages table
    op.drop_index('idx_messages_conversation_id', 'messages')
    op.drop_index('idx_messages_sender_agent_id', 'messages')
    op.drop_index('idx_messages_created_at', 'messages')
    op.drop_index('idx_messages_thread_id', 'messages')
    op.drop_index('idx_messages_parent_id', 'messages')
    op.drop_table('messages')
    
    # Drop conversations table
    op.drop_index('idx_conversations_status', 'conversations')
    op.drop_index('idx_conversations_task_id', 'conversations')
    op.drop_index('idx_conversations_created_by', 'conversations')
    op.drop_index('idx_conversations_created_at', 'conversations')
    op.drop_table('conversations')
```

### Database Backup Script

```python
#!/usr/bin/env python3
"""
Database backup and maintenance script for SwarmDirector
Supports both SQLite and PostgreSQL databases
"""

import argparse
import datetime
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Database backup and maintenance utility"""
    
    def __init__(self, config: dict):
        self.config = config
        self.backup_dir = Path(config.get('backup_dir', 'database/backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, database_url: str) -> Optional[Path]:
        """
        Create database backup
        
        Args:
            database_url: Database connection URL
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            if database_url.startswith('sqlite:'):
                return self._backup_sqlite(database_url)
            elif database_url.startswith('postgresql:'):
                return self._backup_postgresql(database_url)
            else:
                logger.error(f"Unsupported database type: {database_url}")
                return None
                
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def _backup_sqlite(self, database_url: str) -> Optional[Path]:
        """Backup SQLite database"""
        # Extract database path from URL
        db_path = database_url.replace('sqlite:///', '')
        if not db_path.startswith('/'):
            db_path = Path(__file__).parent.parent / db_path
        
        db_file = Path(db_path)
        if not db_file.exists():
            logger.error(f"Database file not found: {db_file}")
            return None
        
        # Create backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"swarm_director_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        # Copy database file
        shutil.copy2(db_file, backup_path)
        
        # Verify backup
        if backup_path.exists() and backup_path.stat().st_size > 0:
            logger.info(f"✅ SQLite backup created: {backup_path}")
            return backup_path
        else:
            logger.error("❌ Backup verification failed")
            return None
    
    def _backup_postgresql(self, database_url: str) -> Optional[Path]:
        """Backup PostgreSQL database"""
        # Create backup filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"swarm_director_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_name
        
        # Use pg_dump to create backup
        cmd = [
            'pg_dump',
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            '--format=plain',
            '--file', str(backup_path),
            database_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ PostgreSQL backup created: {backup_path}")
            return backup_path
        else:
            logger.error(f"❌ pg_dump failed: {result.stderr}")
            return None
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Clean up old backup files
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob('swarm_director_backup_*.db'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"🗑️  Deleted old backup: {backup_file.name}")
        
        for backup_file in self.backup_dir.glob('swarm_director_backup_*.sql'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                deleted_count += 1
                logger.info(f"🗑️  Deleted old backup: {backup_file.name}")
        
        logger.info(f"🧹 Cleaned up {deleted_count} old backup files")
        return deleted_count
    
    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup integrity
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            if backup_path.suffix == '.db':
                return self._verify_sqlite_backup(backup_path)
            elif backup_path.suffix == '.sql':
                return self._verify_postgresql_backup(backup_path)
            else:
                logger.error(f"Unknown backup format: {backup_path}")
                return False
                
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _verify_sqlite_backup(self, backup_path: Path) -> bool:
        """Verify SQLite backup"""
        import sqlite3
        
        try:
            # Try to open and query the backup
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Check if main tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['agents', 'tasks', 'conversations']
            missing_tables = [table for table in required_tables if table not in tables]
            
            conn.close()
            
            if missing_tables:
                logger.error(f"Missing tables in backup: {missing_tables}")
                return False
            
            logger.info("✅ SQLite backup verification passed")
            return True
            
        except Exception as e:
            logger.error(f"SQLite backup verification failed: {e}")
            return False
    
    def _verify_postgresql_backup(self, backup_path: Path) -> bool:
        """Verify PostgreSQL backup"""
        try:
            # Check if file exists and has content
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                logger.error("Backup file is empty or missing")
                return False
            
            # Check for SQL content
            with open(backup_path, 'r') as f:
                content = f.read(1000)  # Read first 1000 characters
                
            if 'CREATE TABLE' not in content and 'INSERT INTO' not in content:
                logger.error("Backup file does not contain expected SQL content")
                return False
            
            logger.info("✅ PostgreSQL backup verification passed")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL backup verification failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SwarmDirector Database Backup Utility")
    
    parser.add_argument(
        '--database-url',
        required=True,
        help='Database connection URL'
    )
    
    parser.add_argument(
        '--backup-dir',
        default='database/backups',
        help='Backup directory (default: database/backups)'
    )
    
    parser.add_argument(
        '--cleanup-days',
        type=int,
        default=30,
        help='Days to keep old backups (default: 30)'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing backups'
    )
    
    parser.add_argument(
        '--cleanup-only',
        action='store_true',
        help='Only cleanup old backups'
    )
    
    args = parser.parse_args()
    
    # Initialize backup utility
    config = {
        'backup_dir': args.backup_dir
    }
    backup_util = DatabaseBackup(config)
    
    if args.cleanup_only:
        # Only cleanup old backups
        backup_util.cleanup_old_backups(args.cleanup_days)
        return
    
    if args.verify_only:
        # Only verify existing backups
        backup_dir = Path(args.backup_dir)
        for backup_file in backup_dir.glob('swarm_director_backup_*'):
            logger.info(f"Verifying {backup_file.name}...")
            if backup_util.verify_backup(backup_file):
                logger.info(f"✅ {backup_file.name} is valid")
            else:
                logger.error(f"❌ {backup_file.name} is invalid")
        return
    
    # Create backup
    logger.info("🔄 Starting database backup...")
    backup_path = backup_util.create_backup(args.database_url)
    
    if backup_path:
        # Verify backup
        if backup_util.verify_backup(backup_path):
            logger.info("✅ Backup created and verified successfully")
        else:
            logger.error("❌ Backup verification failed")
            sys.exit(1)
        
        # Cleanup old backups
        backup_util.cleanup_old_backups(args.cleanup_days)
        
        logger.info("🎉 Backup process completed successfully")
    else:
        logger.error("❌ Backup creation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Related Documentation
- [Database Schema](schemas/database_schema_documented.sql) - Complete schema documentation
- [Migration Guide](../docs/deployment/local_development.md#database-migrations) - Migration procedures
- [Model Documentation](../src/swarm_director/models/DIRECTORY.md) - Database model usage
- [Backup Procedures](../docs/deployment/production_deployment.md#backup-strategy) - Production backup strategies
- [Performance Optimization](../docs/architecture/database_design.md) - Database performance guidelines
