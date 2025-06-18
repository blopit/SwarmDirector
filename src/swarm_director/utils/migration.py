"""
Database Migration Support Module

This module provides comprehensive database migration support including:
- Database abstraction layer for SQLite/PostgreSQL compatibility
- Schema version tracking and validation
- Migration utilities and rollback capabilities
- Data preservation during migrations
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy import text, inspect, MetaData, Table, Column, Integer, String, DateTime, Boolean
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from flask_migrate import upgrade, downgrade, current, stamp, migrate as flask_migrate
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

logger = logging.getLogger(__name__)

class DatabaseMigrationManager:
    """
    Comprehensive database migration management system.
    
    Provides:
    - Schema version tracking
    - Migration execution and rollback
    - Database abstraction layer
    - Data integrity validation
    """
    
    def __init__(self, app=None):
        """Initialize migration manager."""
        self.app = app
        self._migration_dir = None
        self._alembic_config = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        
        # Set migration directory relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self._migration_dir = os.path.join(project_root, 'database', 'migrations')
        
        # Configure Alembic
        self._setup_alembic_config()
        
        # Ensure schema version table exists
        with app.app_context():
            self._ensure_schema_version_table()
        
        # Store in app extensions
        app.extensions['migration_manager'] = self
    
    def _setup_alembic_config(self):
        """Configure Alembic for migrations."""
        alembic_ini_path = os.path.join(self._migration_dir, 'alembic.ini')
        
        if not os.path.exists(alembic_ini_path):
            raise RuntimeError(f"Alembic configuration not found at {alembic_ini_path}")
        
        self._alembic_config = Config(alembic_ini_path)
        self._alembic_config.set_main_option("script_location", self._migration_dir)
    
    def _ensure_schema_version_table(self):
        """Ensure schema version tracking table exists."""
        from ..models.base import db
        
        try:
            # Check if schema_version table exists
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'schema_version' not in tables:
                # Create schema version table
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE schema_version (
                            id INTEGER PRIMARY KEY,
                            version VARCHAR(255) NOT NULL,
                            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            description TEXT,
                            is_current BOOLEAN DEFAULT TRUE
                        )
                    """))
                    conn.commit()
                    
                    # Insert initial version
                    conn.execute(text("""
                        INSERT INTO schema_version (version, description)
                        VALUES ('initial', 'Initial schema version')
                    """))
                    conn.commit()
                    
                logger.info("Created schema_version tracking table")
        
        except SQLAlchemyError as e:
            logger.error(f"Failed to create schema_version table: {e}")
            raise
    
    def get_current_schema_version(self) -> Optional[str]:
        """Get the current schema version."""
        from ..models.base import db
        
        try:
            result = db.session.execute(text("""
                SELECT version FROM schema_version 
                WHERE is_current = TRUE 
                ORDER BY applied_at DESC 
                LIMIT 1
            """)).fetchone()
            
            return result[0] if result else None
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get current schema version: {e}")
            return None
    
    def get_schema_version_history(self) -> List[Dict[str, Any]]:
        """Get schema version history."""
        from ..models.base import db
        
        try:
            results = db.session.execute(text("""
                SELECT version, applied_at, description, is_current
                FROM schema_version
                ORDER BY applied_at DESC
            """)).fetchall()
            
            return [
                {
                    'version': row[0],
                    'applied_at': row[1],
                    'description': row[2],
                    'is_current': bool(row[3])
                }
                for row in results
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get schema version history: {e}")
            return []
    
    def update_schema_version(self, version: str, description: str = None):
        """Update the current schema version."""
        from ..models.base import db
        
        try:
            # Mark all previous versions as not current
            db.session.execute(text("""
                UPDATE schema_version SET is_current = FALSE
            """))
            
            # Insert new version
            db.session.execute(text("""
                INSERT INTO schema_version (version, description, is_current)
                VALUES (:version, :description, TRUE)
            """), {
                'version': version,
                'description': description or f"Migration to {version}"
            })
            
            db.session.commit()
            logger.info(f"Updated schema version to: {version}")
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Failed to update schema version: {e}")
            raise
    
    def validate_schema_integrity(self) -> Dict[str, Any]:
        """Validate database schema integrity."""
        from ..models.base import db
        
        validation_results = {
            'valid': True,
            'issues': [],
            'table_count': 0,
            'missing_tables': [],
            'unexpected_tables': []
        }
        
        try:
            inspector = inspect(db.engine)
            actual_tables = set(inspector.get_table_names())
            validation_results['table_count'] = len(actual_tables)
            
            # Expected tables based on models
            expected_tables = {
                'agents', 'tasks', 'conversations', 'messages',
                'agent_logs', 'schema_version', 'task_analytics',
                'alembic_version'
            }
            
            # Check for missing tables
            missing = expected_tables - actual_tables
            if missing:
                validation_results['missing_tables'] = list(missing)
                validation_results['valid'] = False
                validation_results['issues'].append(f"Missing tables: {missing}")
            
            # Check for unexpected tables (excluding SQLite system tables)
            system_tables = {'sqlite_sequence', 'sqlite_master', 'sqlite_temp_master'}
            unexpected = actual_tables - expected_tables - system_tables
            if unexpected:
                validation_results['unexpected_tables'] = list(unexpected)
                validation_results['issues'].append(f"Unexpected tables: {unexpected}")
            
            logger.info(f"Schema validation completed. Valid: {validation_results['valid']}")
            
        except SQLAlchemyError as e:
            validation_results['valid'] = False
            validation_results['issues'].append(f"Database error: {str(e)}")
            logger.error(f"Schema validation failed: {e}")
        
        return validation_results
    
    def execute_migration(self, target_revision: str = 'head') -> Dict[str, Any]:
        """Execute migration to target revision."""
        migration_result = {
            'success': False,
            'message': '',
            'target_revision': target_revision,
            'previous_version': None,
            'new_version': None
        }
        
        try:
            # Get current version
            migration_result['previous_version'] = self.get_current_schema_version()
            
            # Execute migration using Flask-Migrate
            with self.app.app_context():
                upgrade(directory=self._migration_dir, revision=target_revision)
            
            # Get new version
            migration_result['new_version'] = self.get_current_schema_version()
            migration_result['success'] = True
            migration_result['message'] = f"Migration successful: {migration_result['previous_version']} -> {migration_result['new_version']}"
            
            logger.info(migration_result['message'])
            
        except Exception as e:
            migration_result['message'] = f"Migration failed: {str(e)}"
            logger.error(migration_result['message'])
        
        return migration_result
    
    def rollback_migration(self, target_revision: str) -> Dict[str, Any]:
        """Rollback migration to target revision."""
        rollback_result = {
            'success': False,
            'message': '',
            'target_revision': target_revision,
            'previous_version': None,
            'new_version': None
        }
        
        try:
            # Get current version
            rollback_result['previous_version'] = self.get_current_schema_version()
            
            # Execute rollback using Flask-Migrate
            with self.app.app_context():
                downgrade(directory=self._migration_dir, revision=target_revision)
            
            # Get new version
            rollback_result['new_version'] = self.get_current_schema_version()
            rollback_result['success'] = True
            rollback_result['message'] = f"Rollback successful: {rollback_result['previous_version']} -> {rollback_result['new_version']}"
            
            logger.info(rollback_result['message'])
            
        except Exception as e:
            rollback_result['message'] = f"Rollback failed: {str(e)}"
            logger.error(rollback_result['message'])
        
        return rollback_result
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Dict[str, Any]:
        """Create a new migration script."""
        migration_result = {
            'success': False,
            'message': '',
            'migration_file': None
        }
        
        try:
            with self.app.app_context():
                # Generate migration using Flask-Migrate
                flask_migrate(directory=self._migration_dir, message=message, autogenerate=autogenerate)
            
            migration_result['success'] = True
            migration_result['message'] = f"Migration created: {message}"
            logger.info(migration_result['message'])
            
        except Exception as e:
            migration_result['message'] = f"Failed to create migration: {str(e)}"
            logger.error(migration_result['message'])
        
        return migration_result
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        status = {
            'current_version': self.get_current_schema_version(),
            'alembic_version': None,
            'pending_migrations': [],
            'schema_valid': False
        }
        
        try:
            # Get Alembic version
            with self.app.app_context():
                from ..models.base import db
                result = db.session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                status['alembic_version'] = result[0] if result else None
            
            # Validate schema
            validation = self.validate_schema_integrity()
            status['schema_valid'] = validation['valid']
            status['validation_issues'] = validation.get('issues', [])
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            status['error'] = str(e)
        
        return status


class DataMigrationUtility:
    """
    Utility for handling data preservation and transformation during migrations.
    
    Provides methods for:
    - Data backup and restore
    - Data transformation between schema versions
    - Compatibility layer for PostgreSQL migration
    """
    
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def backup_table_data(self, table_name: str) -> Optional[List[Dict]]:
        """Backup data from a table."""
        try:
            result = self.db.session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            
            # Convert to list of dictionaries
            columns = self.db.session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            column_names = [col[1] for col in columns]
            
            backup_data = []
            for row in result:
                backup_data.append(dict(zip(column_names, row)))
            
            self.logger.info(f"Backed up {len(backup_data)} records from {table_name}")
            return backup_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to backup table {table_name}: {e}")
            return None
    
    def restore_table_data(self, table_name: str, data: List[Dict]) -> bool:
        """Restore data to a table."""
        try:
            if not data:
                return True
            
            # Clear existing data
            self.db.session.execute(text(f"DELETE FROM {table_name}"))
            
            # Insert backup data
            for record in data:
                columns = ', '.join(record.keys())
                placeholders = ', '.join([f":{key}" for key in record.keys()])
                query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                self.db.session.execute(text(query), record)
            
            self.db.session.commit()
            self.logger.info(f"Restored {len(data)} records to {table_name}")
            return True
            
        except SQLAlchemyError as e:
            self.db.session.rollback()
            self.logger.error(f"Failed to restore table {table_name}: {e}")
            return False
    
    def transform_data_for_postgresql(self, data: List[Dict], table_name: str) -> List[Dict]:
        """Transform SQLite data for PostgreSQL compatibility."""
        transformed_data = []
        
        for record in data:
            transformed_record = {}
            for key, value in record.items():
                # Handle boolean values
                if isinstance(value, int) and key.endswith(('_enabled', '_active', '_deleted', 'is_')):
                    transformed_record[key] = bool(value)
                # Handle timestamp formats
                elif key.endswith(('_at', '_time', '_date')) and isinstance(value, str):
                    try:
                        # Convert to proper timestamp format
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        transformed_record[key] = dt
                    except (ValueError, AttributeError):
                        transformed_record[key] = value
                else:
                    transformed_record[key] = value
            
            transformed_data.append(transformed_record)
        
        return transformed_data


# Convenience functions for CLI integration
def init_migration_manager(app):
    """Initialize migration manager with app."""
    return DatabaseMigrationManager(app)

def get_migration_manager():
    """Get migration manager from current app."""
    if not current_app:
        raise RuntimeError("No application context")
    
    return current_app.extensions.get('migration_manager') 