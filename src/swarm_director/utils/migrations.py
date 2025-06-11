"""
Database migration utilities for schema versioning and upgrades
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from flask import current_app
from ..models.base import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class Migration:
    """Represents a single database migration"""
    
    def __init__(self, version: str, description: str, upgrade_sql: List[str], downgrade_sql: List[str] = None):
        self.version = version
        self.description = description
        self.upgrade_sql = upgrade_sql
        self.downgrade_sql = downgrade_sql or []
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert migration to dictionary"""
        return {
            'version': self.version,
            'description': self.description,
            'upgrade_sql': self.upgrade_sql,
            'downgrade_sql': self.downgrade_sql,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Migration':
        """Create migration from dictionary"""
        migration = cls(
            version=data['version'],
            description=data['description'],
            upgrade_sql=data['upgrade_sql'],
            downgrade_sql=data.get('downgrade_sql', [])
        )
        if 'timestamp' in data:
            migration.timestamp = datetime.fromisoformat(data['timestamp'])
        return migration


class MigrationManager:
    """Manages database schema migrations"""
    
    def __init__(self, app=None):
        self.app = app
        self.migrations_dir = None
        self.migrations = []
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.migrations_dir = app.config.get('MIGRATIONS_DIR', 'migrations')
        
        # Ensure migrations directory exists
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Initialize migration tracking table
        self._init_migration_table()
        
        # Load existing migrations
        self._load_migrations()
    
    def _init_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            with self.app.app_context():
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    migration_data TEXT
                )
                """
                with db.engine.connect() as conn:
                    conn.execute(text(create_table_sql))
                    conn.commit()
                logger.info("Migration tracking table initialized")
        except Exception as e:
            logger.error(f"Error initializing migration table: {e}")
    
    def _load_migrations(self):
        """Load migration files from migrations directory"""
        self.migrations = []
        
        if not os.path.exists(self.migrations_dir):
            return
        
        for filename in sorted(os.listdir(self.migrations_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(self.migrations_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        migration_data = json.load(f)
                        migration = Migration.from_dict(migration_data)
                        self.migrations.append(migration)
                except Exception as e:
                    logger.error(f"Error loading migration {filename}: {e}")
    
    def create_migration(self, version: str, description: str, upgrade_sql: List[str], downgrade_sql: List[str] = None) -> Migration:
        """Create a new migration"""
        migration = Migration(version, description, upgrade_sql, downgrade_sql)
        
        # Save migration to file
        filename = f"{version}_{description.lower().replace(' ', '_')}.json"
        filepath = os.path.join(self.migrations_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(migration.to_dict(), f, indent=2)
        
        self.migrations.append(migration)
        logger.info(f"Created migration: {version} - {description}")
        return migration
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        try:
            with self.app.app_context():
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
                    return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        return [migration for migration in self.migrations if migration.version not in applied]
    
    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration"""
        try:
            with self.app.app_context():
                # Begin transaction
                with db.engine.begin() as conn:
                    # Execute upgrade SQL
                    for sql in migration.upgrade_sql:
                        if sql.strip():
                            conn.execute(text(sql))
                    
                    # Record migration as applied
                    conn.execute(text("""
                        INSERT INTO schema_migrations (version, description, migration_data)
                        VALUES (:version, :description, :data)
                    """), {
                        'version': migration.version,
                        'description': migration.description,
                        'data': json.dumps(migration.to_dict())
                    })
                
                logger.info(f"Applied migration: {migration.version} - {migration.description}")
                return True
        except Exception as e:
            logger.error(f"Error applying migration {migration.version}: {e}")
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        try:
            # Find migration
            migration = None
            for m in self.migrations:
                if m.version == version:
                    migration = m
                    break
            
            if not migration:
                logger.error(f"Migration {version} not found")
                return False
            
            if not migration.downgrade_sql:
                logger.error(f"Migration {version} has no downgrade SQL")
                return False
            
            with self.app.app_context():
                # Begin transaction
                with db.engine.begin() as conn:
                    # Execute downgrade SQL
                    for sql in migration.downgrade_sql:
                        if sql.strip():
                            conn.execute(text(sql))
                    
                    # Remove migration record
                    conn.execute(text("DELETE FROM schema_migrations WHERE version = :version"), {
                        'version': version
                    })
                
                logger.info(f"Rolled back migration: {version}")
                return True
        except Exception as e:
            logger.error(f"Error rolling back migration {version}: {e}")
            return False
    
    def migrate_to_latest(self) -> bool:
        """Apply all pending migrations"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        success_count = 0
        for migration in pending:
            if self.apply_migration(migration):
                success_count += 1
            else:
                logger.error(f"Failed to apply migration {migration.version}, stopping")
                break
        
        logger.info(f"Applied {success_count} migrations")
        return success_count == len(pending)
    
    def migrate_to_version(self, target_version: str) -> bool:
        """Migrate to a specific version"""
        applied = self.get_applied_migrations()
        current_version = applied[-1] if applied else None
        
        if current_version == target_version:
            logger.info(f"Already at version {target_version}")
            return True
        
        # Find target migration
        target_migration = None
        for migration in self.migrations:
            if migration.version == target_version:
                target_migration = migration
                break
        
        if not target_migration:
            logger.error(f"Target version {target_version} not found")
            return False
        
        # Determine direction (upgrade or downgrade)
        if not current_version or target_version > current_version:
            # Upgrade
            pending = self.get_pending_migrations()
            for migration in pending:
                if migration.version <= target_version:
                    if not self.apply_migration(migration):
                        return False
                else:
                    break
        else:
            # Downgrade
            for version in reversed(applied):
                if version > target_version:
                    if not self.rollback_migration(version):
                        return False
        
        return True
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            'current_version': applied[-1] if applied else None,
            'applied_count': len(applied),
            'pending_count': len(pending),
            'applied_migrations': applied,
            'pending_migrations': [{'version': m.version, 'description': m.description} for m in pending],
            'total_migrations': len(self.migrations)
        }
    
    def generate_initial_migration(self) -> Migration:
        """Generate initial migration from current schema"""
        try:
            with self.app.app_context():
                # Get current schema
                schema_sql = []
                
                with db.engine.connect() as conn:
                    # Get all tables
                    result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"))
                    for row in result.fetchall():
                        if row[0]:
                            schema_sql.append(row[0] + ";")
                    
                    # Get all indexes
                    result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"))
                    for row in result.fetchall():
                        if row[0]:
                            schema_sql.append(row[0] + ";")
                
                # Create initial migration
                migration = self.create_migration(
                    version="001_initial_schema",
                    description="Initial database schema",
                    upgrade_sql=schema_sql,
                    downgrade_sql=["DROP TABLE IF EXISTS schema_migrations;"]
                )
                
                return migration
        except Exception as e:
            logger.error(f"Error generating initial migration: {e}")
            return None


# Global instance
migration_manager = MigrationManager()


def init_migration_manager(app):
    """Initialize migration manager with Flask app"""
    migration_manager.init_app(app)
    return migration_manager


# Predefined migrations for common operations
def create_index_migration(table_name: str, column_name: str, index_name: str = None) -> Migration:
    """Create a migration for adding an index"""
    if not index_name:
        index_name = f"idx_{table_name}_{column_name}"
    
    upgrade_sql = [f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name});"]
    downgrade_sql = [f"DROP INDEX IF EXISTS {index_name};"]
    
    return Migration(
        version=f"add_index_{index_name}",
        description=f"Add index {index_name} on {table_name}.{column_name}",
        upgrade_sql=upgrade_sql,
        downgrade_sql=downgrade_sql
    )


def add_column_migration(table_name: str, column_name: str, column_type: str, default_value: str = None) -> Migration:
    """Create a migration for adding a column"""
    upgrade_sql = [f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"]
    if default_value:
        upgrade_sql[0] += f" DEFAULT {default_value}"
    upgrade_sql[0] += ";"
    
    # Note: SQLite doesn't support DROP COLUMN, so downgrade would require table recreation
    downgrade_sql = [f"-- Cannot drop column {column_name} from {table_name} in SQLite"]
    
    return Migration(
        version=f"add_column_{table_name}_{column_name}",
        description=f"Add column {column_name} to {table_name}",
        upgrade_sql=upgrade_sql,
        downgrade_sql=downgrade_sql
    ) 