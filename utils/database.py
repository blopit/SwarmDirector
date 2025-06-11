"""
Database utility functions for SwarmDirector
"""

import os
from flask import current_app
from models.base import db

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
        from models.agent import Agent, AgentType, AgentStatus
        from models.task import Task, TaskStatus, TaskPriority
        
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