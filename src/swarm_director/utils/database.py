"""
Database utilities for migration, optimization, and maintenance
"""

import os
import sqlite3
import shutil
import json
from datetime import datetime, timedelta
from flask import current_app
from ..models.base import db
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Comprehensive database management utilities"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        # Extract database path from SQLALCHEMY_DATABASE_URI
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///swarm_director.db')
        if db_uri.startswith('sqlite:///'):
            relative_path = db_uri.replace('sqlite:///', '')
            # Check if it's an absolute path or relative to instance folder
            if not os.path.isabs(relative_path):
                self.db_path = os.path.join(app.instance_path, relative_path)
            else:
                self.db_path = relative_path
        else:
            self.db_path = app.config.get('DATABASE_PATH', 'swarm_director.db')
        
        self.backup_dir = app.config.get('BACKUP_DIR', 'backups')
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Ensure instance directory exists
        os.makedirs(app.instance_path, exist_ok=True)
    
    def create_tables(self):
        """Create all database tables"""
        try:
            with self.app.app_context():
                db.create_all()
                logger.info("Database tables created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables"""
        try:
            with self.app.app_context():
                db.drop_all()
                logger.info("Database tables dropped successfully")
                return True
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            return False
    
    def recreate_database(self):
        """Drop and recreate all tables"""
        try:
            self.drop_tables()
            self.create_tables()
            logger.info("Database recreated successfully")
            return True
        except Exception as e:
            logger.error(f"Error recreating database: {e}")
            return False
    
    def backup_database(self, backup_name=None):
        """Create a backup of the database"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}.db"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            shutil.copy2(self.db_path, backup_path)
            
            # Create metadata file
            metadata = {
                'backup_name': backup_name,
                'original_db': self.db_path,
                'created_at': datetime.now().isoformat(),
                'size_bytes': os.path.getsize(backup_path)
            }
            
            metadata_path = backup_path.replace('.db', '.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return None
    
    def restore_database(self, backup_path):
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create backup of current database before restore
            current_backup = self.backup_database(f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def optimize_database(self):
        """Optimize database performance"""
        try:
            with self.app.app_context():
                # Run VACUUM to reclaim space and defragment
                with db.engine.connect() as conn:
                    conn.execute(text("VACUUM"))
                    
                    # Update table statistics
                    conn.execute(text("ANALYZE"))
                    
                    # Set optimal SQLite pragmas for performance
                    optimizations = [
                        "PRAGMA journal_mode=WAL",
                        "PRAGMA synchronous=NORMAL", 
                        "PRAGMA cache_size=10000",
                        "PRAGMA temp_store=MEMORY",
                        "PRAGMA mmap_size=268435456"  # 256MB
                    ]
                    
                    for pragma in optimizations:
                        conn.execute(text(pragma))
                
                logger.info("Database optimization completed")
                return True
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            return False
    
    def create_indexes(self):
        """Create performance indexes"""
        try:
            with self.app.app_context():
                indexes = [
                    # Agent indexes
                    "CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type)",
                    "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)",
                    "CREATE INDEX IF NOT EXISTS idx_agents_parent ON agents(parent_id)",
                    
                    # Task indexes
                    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_agent_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)",
                    
                    # AgentLog indexes
                    "CREATE INDEX IF NOT EXISTS idx_agent_logs_task ON agent_logs(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_id)",
                    "CREATE INDEX IF NOT EXISTS idx_agent_logs_level ON agent_logs(log_level)",
                    "CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at)",
                    
                    # Draft indexes
                    "CREATE INDEX IF NOT EXISTS idx_drafts_task ON drafts(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)",
                    "CREATE INDEX IF NOT EXISTS idx_drafts_version ON drafts(task_id, version)",
                    "CREATE INDEX IF NOT EXISTS idx_drafts_author ON drafts(author_agent_id)",
                    
                    # EmailMessage indexes
                    "CREATE INDEX IF NOT EXISTS idx_email_task ON email_messages(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_email_status ON email_messages(status)",
                    "CREATE INDEX IF NOT EXISTS idx_email_recipient ON email_messages(recipient)",
                    "CREATE INDEX IF NOT EXISTS idx_email_sent ON email_messages(sent_at)",
                    
                    # Conversation indexes
                    "CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status)",
                    "CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)",
                    "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
                    
                    # Message indexes
                    "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)",
                    "CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_agent_id)",
                    "CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type)",
                    "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)"
                ]
                
                with db.engine.connect() as conn:
                    for index_sql in indexes:
                        conn.execute(text(index_sql))
                
                logger.info("Performance indexes created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
    
    def get_database_stats(self):
        """Get database statistics and health information"""
        try:
            with self.app.app_context():
                stats = {}
                
                # Get table counts
                inspector = inspect(db.engine)
                table_names = inspector.get_table_names()
                
                with db.engine.connect() as conn:
                    for table in table_names:
                        try:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.scalar()
                            stats[f"{table}_count"] = count
                        except Exception as e:
                            stats[f"{table}_count"] = f"Error: {e}"
                    
                    # Get SQLite version and pragma info
                    result = conn.execute(text("SELECT sqlite_version()"))
                    stats['sqlite_version'] = result.scalar()
                    
                    pragma_info = {}
                    pragmas = ['journal_mode', 'synchronous', 'cache_size', 'page_size', 'page_count']
                    for pragma in pragmas:
                        try:
                            result = conn.execute(text(f"PRAGMA {pragma}"))
                            pragma_info[pragma] = result.scalar()
                        except:
                            pragma_info[pragma] = "N/A"
                
                # Get database file size
                if os.path.exists(self.db_path):
                    stats['database_size_bytes'] = os.path.getsize(self.db_path)
                    stats['database_size_mb'] = round(stats['database_size_bytes'] / 1024 / 1024, 2)
                
                stats['pragma_info'] = pragma_info
                stats['last_updated'] = datetime.now().isoformat()
                
                return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
    
    def check_database_integrity(self):
        """Check database integrity"""
        try:
            with self.app.app_context():
                with db.engine.connect() as conn:
                    # Run integrity check
                    result = conn.execute(text("PRAGMA integrity_check"))
                    integrity_result = result.fetchall()
                    
                    # Run foreign key check
                    result = conn.execute(text("PRAGMA foreign_key_check"))
                    fk_violations = result.fetchall()
                
                return {
                    'integrity_ok': len(integrity_result) == 1 and integrity_result[0][0] == 'ok',
                    'integrity_details': [row[0] for row in integrity_result],
                    'foreign_key_violations': [dict(row) for row in fk_violations],
                    'checked_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error checking database integrity: {e}")
            return {'error': str(e)}
    
    def cleanup_old_logs(self, days_to_keep=30):
        """Clean up old log entries"""
        try:
            with self.app.app_context():
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)
                
                # Clean up old agent logs
                from ..models.agent_log import AgentLog
                old_logs = AgentLog.query.filter(AgentLog.created_at < cutoff_date).all()
                count = len(old_logs)
                
                for log in old_logs:
                    db.session.delete(log)
                
                db.session.commit()
                logger.info(f"Cleaned up {count} old log entries")
                return count
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0
    
    def get_query_suggestions(self):
        """Get query optimization suggestions"""
        suggestions = []
        
        try:
            with self.app.app_context():
                stats = self.get_database_stats()
                
                # Check for missing indexes based on table sizes
                if stats.get('tasks_count', 0) > 1000:
                    suggestions.append("Consider adding composite indexes for frequent task queries")
                
                if stats.get('agent_logs_count', 0) > 10000:
                    suggestions.append("Consider partitioning agent_logs table by date")
                
                if stats.get('database_size_mb', 0) > 100:
                    suggestions.append("Consider running VACUUM to reclaim space")
                
                # Check pragma settings
                pragma_info = stats.get('pragma_info', {})
                if pragma_info.get('journal_mode') != 'wal':
                    suggestions.append("Enable WAL mode for better concurrency")
                
                if pragma_info.get('synchronous') == 'FULL':
                    suggestions.append("Consider setting synchronous=NORMAL for better performance")
                
                return suggestions
        except Exception as e:
            logger.error(f"Error generating query suggestions: {e}")
            return [f"Error generating suggestions: {e}"]


# Global instance
db_manager = DatabaseManager()


def init_database_manager(app):
    """Initialize database manager with Flask app"""
    db_manager.init_app(app)
    return db_manager

def init_db():
    """Initialize the database with all tables"""
    try:
        # Create all tables
        db.create_all()
        current_app.logger.info("Database tables created successfully")
        
        # Run any initial data setup
        create_initial_data()
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error initializing database: {str(e)}")
        return False

def reset_db():
    """Reset the database by dropping and recreating all tables"""
    try:
        # Drop all tables
        db.drop_all()
        current_app.logger.info("Database tables dropped")
        
        # Recreate all tables
        db.create_all()
        current_app.logger.info("Database tables recreated")
        
        # Run initial data setup
        create_initial_data()
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error resetting database: {str(e)}")
        return False

def create_initial_data():
    """Create initial data for the application"""
    try:
        from ..models.agent import Agent, AgentType, AgentStatus
        from ..models.task import Task, TaskStatus, TaskPriority
        
        # Check if we already have data
        if Agent.query.first() is not None:
            current_app.logger.info("Initial data already exists, skipping creation")
            return
        
        # Create a default supervisor agent
        supervisor = Agent(
            name="Main Supervisor",
            description="Primary supervisor agent for coordinating the swarm",
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.ACTIVE,
            capabilities=["coordination", "task_assignment", "monitoring"],
            system_message="You are the main supervisor agent responsible for coordinating other agents and managing task assignments."
        )
        supervisor.save()
        
        # Create a sample task
        sample_task = Task(
            title="Initialize Agent System",
            description="Set up the basic agent system and verify all components are working",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            input_data={"type": "system_initialization"}
        )
        sample_task.save()
        
        current_app.logger.info("Initial data created successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error creating initial data: {str(e)}")

def backup_database(backup_path=None):
    """Create a backup of the database"""
    if backup_path is None:
        backup_path = f"backup_{current_app.config['SQLALCHEMY_DATABASE_URI'].split('/')[-1]}"
    
    try:
        # For SQLite databases, we can copy the file
        if 'sqlite' in current_app.config['SQLALCHEMY_DATABASE_URI']:
            import shutil
            db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            shutil.copy2(db_path, backup_path)
            current_app.logger.info(f"Database backup created: {backup_path}")
            return True
        else:
            current_app.logger.warning("Database backup not implemented for non-SQLite databases")
            return False
    except Exception as e:
        current_app.logger.error(f"Error creating database backup: {str(e)}")
        return False

def get_database_info():
    """Get information about the database"""
    try:
        info = {
            'database_uri': current_app.config['SQLALCHEMY_DATABASE_URI'],
            'tables': []
        }
        
        # Get table information
        for table in db.metadata.tables.values():
            table_info = {
                'name': table.name,
                'columns': [col.name for col in table.columns]
            }
            info['tables'].append(table_info)
        
        return info
    except Exception as e:
        current_app.logger.error(f"Error getting database info: {str(e)}")
        return None 