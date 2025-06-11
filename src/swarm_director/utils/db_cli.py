"""
Command-line interface for database management operations
"""

import click
import os
from flask import Flask
from flask.cli import with_appcontext
from .database import db_manager, init_database_manager
from .migrations import migration_manager, init_migration_manager
from ..models.base import db
import json
from datetime import datetime

def init_db_cli(app):
    """Initialize database CLI commands"""
    
    @app.cli.group()
    def database():
        """Database management commands"""
        pass
    
    @database.command()
    @with_appcontext
    def init():
        """Initialize the database with all tables"""
        if db_manager.create_tables():
            click.echo("✅ Database initialized successfully")
        else:
            click.echo("❌ Failed to initialize database")
    
    @database.command()
    @with_appcontext
    def recreate():
        """Drop and recreate all database tables"""
        if click.confirm('This will delete all data. Are you sure?'):
            if db_manager.recreate_database():
                click.echo("✅ Database recreated successfully")
            else:
                click.echo("❌ Failed to recreate database")
    
    @database.command()
    @click.option('--name', help='Backup filename')
    @with_appcontext
    def backup(name):
        """Create a database backup"""
        backup_path = db_manager.backup_database(name)
        if backup_path:
            click.echo(f"✅ Database backed up to: {backup_path}")
        else:
            click.echo("❌ Failed to create backup")
    
    @database.command()
    @click.argument('backup_path')
    @with_appcontext
    def restore(backup_path):
        """Restore database from backup"""
        if click.confirm(f'This will restore from {backup_path} and overwrite current data. Continue?'):
            if db_manager.restore_database(backup_path):
                click.echo("✅ Database restored successfully")
            else:
                click.echo("❌ Failed to restore database")
    
    @database.command()
    @with_appcontext
    def optimize():
        """Optimize database performance"""
        if db_manager.optimize_database():
            click.echo("✅ Database optimization completed")
        else:
            click.echo("❌ Failed to optimize database")
    
    @database.command()
    @with_appcontext
    def create_indexes():
        """Create performance indexes"""
        if db_manager.create_indexes():
            click.echo("✅ Performance indexes created")
        else:
            click.echo("❌ Failed to create indexes")
    
    @database.command()
    @with_appcontext
    def stats():
        """Show database statistics"""
        stats = db_manager.get_database_stats()
        
        if 'error' in stats:
            click.echo(f"❌ Error getting stats: {stats['error']}")
            return
        
        click.echo("\n📊 Database Statistics:")
        click.echo(f"SQLite Version: {stats.get('sqlite_version', 'Unknown')}")
        click.echo(f"Database Size: {stats.get('database_size_mb', 0)} MB")
        
        click.echo("\n📋 Table Counts:")
        for key, value in stats.items():
            if key.endswith('_count'):
                table_name = key.replace('_count', '')
                click.echo(f"  {table_name}: {value}")
        
        pragma_info = stats.get('pragma_info', {})
        if pragma_info:
            click.echo("\n⚙️ SQLite Configuration:")
            for key, value in pragma_info.items():
                click.echo(f"  {key}: {value}")
    
    @database.command()
    @with_appcontext
    def integrity():
        """Check database integrity"""
        result = db_manager.check_database_integrity()
        
        if 'error' in result:
            click.echo(f"❌ Error checking integrity: {result['error']}")
            return
        
        if result.get('integrity_ok'):
            click.echo("✅ Database integrity check passed")
        else:
            click.echo("❌ Database integrity issues found:")
            for detail in result.get('integrity_details', []):
                click.echo(f"  - {detail}")
        
        violations = result.get('foreign_key_violations', [])
        if violations:
            click.echo(f"\n⚠️ Foreign key violations found ({len(violations)}):")
            for violation in violations:
                click.echo(f"  - {violation}")
        else:
            click.echo("✅ No foreign key violations")
    
    @database.command()
    @click.option('--days', default=30, help='Days of logs to keep')
    @with_appcontext
    def cleanup(days):
        """Clean up old log entries"""
        count = db_manager.cleanup_old_logs(days)
        click.echo(f"✅ Cleaned up {count} old log entries")
    
    @database.command()
    @with_appcontext
    def suggestions():
        """Get query optimization suggestions"""
        suggestions = db_manager.get_query_suggestions()
        
        if suggestions:
            click.echo("\n💡 Optimization Suggestions:")
            for suggestion in suggestions:
                click.echo(f"  - {suggestion}")
        else:
            click.echo("✅ No optimization suggestions at this time")
    
    # Migration commands
    @app.cli.group()
    def migrate():
        """Database migration commands"""
        pass
    
    @migrate.command()
    @with_appcontext
    def status():
        """Show migration status"""
        status = migration_manager.get_migration_status()
        
        click.echo(f"\n📊 Migration Status:")
        click.echo(f"Current Version: {status.get('current_version', 'None')}")
        click.echo(f"Applied Migrations: {status.get('applied_count', 0)}")
        click.echo(f"Pending Migrations: {status.get('pending_count', 0)}")
        
        pending = status.get('pending_migrations', [])
        if pending:
            click.echo("\n⏳ Pending Migrations:")
            for migration in pending:
                click.echo(f"  - {migration['version']}: {migration['description']}")
    
    @migrate.command()
    @with_appcontext
    def upgrade():
        """Apply all pending migrations"""
        if migration_manager.migrate_to_latest():
            click.echo("✅ All migrations applied successfully")
        else:
            click.echo("❌ Migration failed")
    
    @migrate.command()
    @click.argument('version')
    @with_appcontext
    def to_version(version):
        """Migrate to a specific version"""
        if migration_manager.migrate_to_version(version):
            click.echo(f"✅ Migrated to version {version}")
        else:
            click.echo(f"❌ Failed to migrate to version {version}")
    
    @migrate.command()
    @click.argument('version')
    @with_appcontext
    def rollback(version):
        """Rollback a specific migration"""
        if click.confirm(f'This will rollback migration {version}. Continue?'):
            if migration_manager.rollback_migration(version):
                click.echo(f"✅ Rolled back migration {version}")
            else:
                click.echo(f"❌ Failed to rollback migration {version}")
    
    @migrate.command()
    @click.argument('version')
    @click.argument('description')
    @click.option('--sql-file', help='File containing upgrade SQL')
    @with_appcontext
    def create(version, description, sql_file):
        """Create a new migration"""
        upgrade_sql = []
        
        if sql_file and os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                content = f.read()
                # Split by semicolon and filter empty statements
                upgrade_sql = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
        else:
            click.echo("Please provide SQL statements (enter empty line to finish):")
            while True:
                stmt = click.prompt("SQL", default="", show_default=False)
                if not stmt:
                    break
                upgrade_sql.append(stmt)
        
        if upgrade_sql:
            migration = migration_manager.create_migration(version, description, upgrade_sql)
            click.echo(f"✅ Created migration: {migration.version}")
        else:
            click.echo("❌ No SQL statements provided")
    
    @migrate.command()
    @with_appcontext
    def init_schema():
        """Generate initial migration from current schema"""
        if click.confirm('This will generate a migration from the current schema. Continue?'):
            migration = migration_manager.generate_initial_migration()
            if migration:
                click.echo(f"✅ Generated initial migration: {migration.version}")
            else:
                click.echo("❌ Failed to generate initial migration")


def create_db_management_script():
    """Create a standalone database management script"""
    script_content = '''#!/usr/bin/env python
"""
Standalone database management script for SwarmDirector
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from utils.database import init_database_manager
from utils.migrations import init_migration_manager
from utils.db_cli import init_db_cli

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database utilities
    init_database_manager(app)
    init_migration_manager(app)
    init_db_cli(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        import click
        from utils.database import db_manager
        from utils.migrations import migration_manager
        
        @click.group()
        def cli():
            """SwarmDirector Database Management"""
            pass
        
        @cli.command()
        def status():
            """Show database and migration status"""
            click.echo("🗄️ SwarmDirector Database Status\\n")
            
            # Database stats
            stats = db_manager.get_database_stats()
            if 'error' not in stats:
                click.echo(f"Database Size: {stats.get('database_size_mb', 0)} MB")
                click.echo(f"SQLite Version: {stats.get('sqlite_version', 'Unknown')}")
            
            # Migration status
            migration_status = migration_manager.get_migration_status()
            click.echo(f"Current Schema Version: {migration_status.get('current_version', 'None')}")
            click.echo(f"Pending Migrations: {migration_status.get('pending_count', 0)}")
        
        @cli.command()
        def setup():
            """Setup database with initial schema"""
            click.echo("Setting up SwarmDirector database...")
            
            if db_manager.create_tables():
                click.echo("✅ Database tables created")
            else:
                click.echo("❌ Failed to create tables")
                return
            
            if db_manager.create_indexes():
                click.echo("✅ Performance indexes created")
            else:
                click.echo("⚠️ Warning: Failed to create some indexes")
            
            if db_manager.optimize_database():
                click.echo("✅ Database optimized")
            
            click.echo("\\n🎉 Database setup complete!")
        
        cli()
'''
    
    with open('manage_db.py', 'w') as f:
        f.write(script_content)
    
    # Make it executable
    os.chmod('manage_db.py', 0o755)
    
    return 'manage_db.py' 