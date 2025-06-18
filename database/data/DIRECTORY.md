---
title: Database Data Directory
description: Database files and data storage for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [database, data-storage, sqlite, backups]
---

# Database Data Directory

## Purpose

The database/data directory contains the actual database files, backups, and data storage for SwarmDirector. This directory serves as the primary data persistence layer for development and testing environments, storing all application data including agents, tasks, conversations, analytics, and system state.

## Structure

```
database/data/
├── swarm_director_dev.db        # Main development database (SQLite)
├── swarm_director_test.db       # Test database (created during testing)
├── swarm_director_dev_backup.db # Development database backup
├── backups/                     # Database backup files
│   ├── daily/                   # Daily automated backups
│   │   ├── swarm_director_2025_06_18.db
│   │   ├── swarm_director_2025_06_17.db
│   │   └── swarm_director_2025_06_16.db
│   ├── weekly/                  # Weekly backup archives
│   │   ├── swarm_director_week_25.db
│   │   └── swarm_director_week_24.db
│   └── manual/                  # Manual backup files
│       ├── pre_migration_backup.db
│       └── feature_test_backup.db
├── exports/                     # Data export files
│   ├── agents_export.json       # Agent configuration exports
│   ├── tasks_export.csv         # Task data exports
│   ├── analytics_export.json    # Analytics data exports
│   └── conversations_export.json # Conversation exports
├── imports/                     # Data import staging
│   ├── agent_configs.json       # Agent configurations to import
│   ├── sample_tasks.csv         # Sample task data
│   └── test_data.json           # Test data for development
└── temp/                        # Temporary database files
    ├── migration_temp.db        # Temporary files during migrations
    ├── backup_temp.db           # Temporary backup files
    └── import_temp.db           # Temporary import processing files
```

## Guidelines

### 1. Organization
- **Environment Separation**: Separate database files by environment (dev, test, prod)
- **Backup Strategy**: Implement automated and manual backup procedures
- **Data Export**: Provide data export capabilities for analysis and migration
- **Import Staging**: Stage import data before processing

### 2. Naming
- **Database Files**: Use descriptive names with environment suffix (e.g., `swarm_director_dev.db`)
- **Backup Files**: Include timestamp in backup file names
- **Export Files**: Use format-specific extensions (`.json`, `.csv`, `.sql`)
- **Temporary Files**: Use `_temp` suffix for temporary files

### 3. Implementation
- **SQLite for Development**: Use SQLite for development and testing environments
- **Backup Automation**: Implement automated backup procedures
- **Data Integrity**: Ensure data integrity through proper constraints and validation
- **Performance**: Optimize database performance with proper indexing
- **Security**: Implement proper access controls and encryption for sensitive data

### 4. Documentation
- **Database Schema**: Document database schema and relationships
- **Backup Procedures**: Document backup and restore procedures
- **Data Migration**: Document data migration processes
- **Performance Tuning**: Document performance optimization strategies

## Best Practices

### Database Management
```python
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / "backups" / "daily"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create a backup of the database."""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            backup_name = f"swarm_director_backup_{timestamp}.db"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create current backup before restore
            self.create_backup("pre_restore_backup.db")
            
            # Restore from backup
            shutil.copy2(backup_file, self.db_path)
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def vacuum_database(self) -> bool:
        """Optimize database by running VACUUM."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
            logger.info("Database vacuum completed")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
```

### Security
- **Access Control**: Implement proper file system permissions for database files
- **Encryption**: Use encryption for sensitive data in production environments
- **Backup Security**: Secure backup files with appropriate permissions
- **Audit Logging**: Log all database access and modifications

### Performance
- **Indexing**: Create appropriate indexes for frequently queried columns
- **Connection Pooling**: Use connection pooling for better performance
- **Query Optimization**: Optimize database queries for better performance
- **Regular Maintenance**: Perform regular database maintenance (VACUUM, ANALYZE)

### Testing
```python
import pytest
import tempfile
from pathlib import Path
from src.swarm_director.utils.database import DatabaseManager

@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_db_path = temp_file.name
    
    # Initialize test database
    db_manager = DatabaseManager(temp_db_path)
    yield temp_db_path
    
    # Cleanup
    Path(temp_db_path).unlink(missing_ok=True)

def test_database_backup_creation(temp_database):
    """Test database backup creation."""
    db_manager = DatabaseManager(temp_database)
    
    # Create backup
    backup_path = db_manager.create_backup("test_backup.db")
    
    # Verify backup exists
    assert Path(backup_path).exists()
    assert Path(backup_path).stat().st_size > 0

def test_database_restore(temp_database):
    """Test database restore from backup."""
    db_manager = DatabaseManager(temp_database)
    
    # Create initial backup
    backup_path = db_manager.create_backup("restore_test.db")
    
    # Modify database (simulate changes)
    # ... database modifications ...
    
    # Restore from backup
    result = db_manager.restore_backup(backup_path)
    assert result is True
```

### Backup Strategy
- **Automated Backups**: Implement automated daily and weekly backups
- **Retention Policy**: Define backup retention policies (daily for 30 days, weekly for 12 weeks)
- **Backup Verification**: Verify backup integrity regularly
- **Offsite Storage**: Store backups in offsite locations for disaster recovery

## Examples

### Database Initialization
```python
import sqlite3
from pathlib import Path

def initialize_database(db_path: str) -> bool:
    """Initialize a new database with required tables."""
    try:
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create tables (this would typically use migration scripts)
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 3,
                    assigned_agent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (assigned_agent_id) REFERENCES agents (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority);
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks (assigned_agent_id);
            """)
            
            conn.commit()
            
        logger.info(f"Database initialized: {db_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
```

### Data Export Utility
```python
import json
import csv
from typing import List, Dict, Any

class DataExporter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.export_dir = Path(db_path).parent / "exports"
        self.export_dir.mkdir(exist_ok=True)
    
    def export_agents_to_json(self) -> str:
        """Export agents to JSON format."""
        export_file = self.export_dir / "agents_export.json"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, name, type, config, created_at, updated_at
                FROM agents
                ORDER BY created_at
            """)
            
            agents = []
            for row in cursor.fetchall():
                agent = {
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "config": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4],
                    "updated_at": row[5]
                }
                agents.append(agent)
        
        with open(export_file, 'w') as f:
            json.dump(agents, f, indent=2, default=str)
        
        return str(export_file)
    
    def export_tasks_to_csv(self) -> str:
        """Export tasks to CSV format."""
        export_file = self.export_dir / "tasks_export.csv"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT t.id, t.title, t.description, t.status, t.priority,
                       a.name as agent_name, t.created_at, t.updated_at
                FROM tasks t
                LEFT JOIN agents a ON t.assigned_agent_id = a.id
                ORDER BY t.created_at
            """)
            
            with open(export_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'ID', 'Title', 'Description', 'Status', 'Priority',
                    'Agent Name', 'Created At', 'Updated At'
                ])
                
                # Write data
                for row in cursor.fetchall():
                    writer.writerow(row)
        
        return str(export_file)
```

### Database Health Check
```python
def check_database_health(db_path: str) -> Dict[str, Any]:
    """Perform database health check."""
    health_status = {
        "status": "healthy",
        "issues": [],
        "statistics": {},
        "recommendations": []
    }
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Check database integrity
            integrity_check = conn.execute("PRAGMA integrity_check").fetchone()
            if integrity_check[0] != "ok":
                health_status["status"] = "unhealthy"
                health_status["issues"].append(f"Integrity check failed: {integrity_check[0]}")
            
            # Get database statistics
            stats = {}
            
            # Database size
            db_size = Path(db_path).stat().st_size
            stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
            
            # Table counts
            tables = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """).fetchall()
            
            for table in tables:
                table_name = table[0]
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                stats[f"{table_name}_count"] = count
            
            health_status["statistics"] = stats
            
            # Performance recommendations
            if db_size > 100 * 1024 * 1024:  # 100MB
                health_status["recommendations"].append("Consider running VACUUM to optimize database")
            
            if stats.get("tasks_count", 0) > 10000:
                health_status["recommendations"].append("Consider archiving old completed tasks")
    
    except Exception as e:
        health_status["status"] = "error"
        health_status["issues"].append(f"Health check failed: {e}")
    
    return health_status
```

## Related Documentation

- [Database Schema](../schemas/README.md) - Database schema documentation
- [Migration Guide](../migrations/README.md) - Database migration procedures
- [Backup Procedures](../../docs/development/backup_procedures.md) - Backup and restore guide
- [Performance Tuning](../../docs/development/database_performance.md) - Database performance optimization
- [Security Guide](../../docs/development/database_security.md) - Database security best practices
- [Testing Guide](../../docs/development/database_testing.md) - Database testing procedures
