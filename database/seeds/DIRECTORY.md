---
title: Database Seeds Directory
description: Database seeding scripts and sample data for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [database-seeds, sample-data, test-data, initialization]
---

# Database Seeds Directory

## Purpose

The database/seeds directory contains database seeding scripts, sample data, and initialization data for SwarmDirector. This directory provides consistent data setup for development, testing, and demonstration environments, ensuring that developers and testers have access to realistic and comprehensive sample data.

## Structure

```
database/seeds/
├── README.md                    # Seeding documentation and procedures
├── seed_runner.py               # Main seeding script runner
├── development/                 # Development environment seeds
│   ├── 001_initial_agents.sql   # Initial agent configurations
│   ├── 002_sample_tasks.sql     # Sample task data
│   ├── 003_conversations.sql    # Sample conversation data
│   ├── 004_analytics_data.sql   # Sample analytics data
│   └── 005_workflow_data.sql    # Sample workflow data
├── testing/                     # Test environment seeds
│   ├── test_agents.sql          # Test agent configurations
│   ├── test_tasks.sql           # Test task scenarios
│   ├── test_conversations.sql   # Test conversation data
│   ├── test_edge_cases.sql      # Edge case test data
│   └── performance_test_data.sql # Performance testing data
├── demo/                        # Demo environment seeds
│   ├── demo_agents.sql          # Demo agent configurations
│   ├── demo_scenarios.sql       # Demo task scenarios
│   ├── demo_conversations.sql   # Demo conversation flows
│   └── demo_analytics.sql       # Demo analytics data
├── production/                  # Production initialization seeds
│   ├── default_agents.sql       # Default production agents
│   ├── system_config.sql        # System configuration data
│   └── initial_users.sql        # Initial user accounts
├── utilities/                   # Seeding utilities
│   ├── data_generator.py        # Synthetic data generation
│   ├── csv_importer.py          # CSV data import utility
│   ├── json_importer.py         # JSON data import utility
│   └── data_validator.py        # Seed data validation
└── fixtures/                    # Data fixture files
    ├── agents.json              # Agent fixture data
    ├── tasks.json               # Task fixture data
    ├── conversations.json       # Conversation fixture data
    └── workflows.json           # Workflow fixture data
```

## Guidelines

### 1. Organization
- **Environment Separation**: Separate seeds by environment (development, testing, demo, production)
- **Sequential Ordering**: Use numbered prefixes for execution order
- **Data Relationships**: Maintain referential integrity in seed data
- **Modular Design**: Create modular, reusable seed components

### 2. Naming
- **Seed Files**: Use descriptive names with sequential prefixes (e.g., `001_initial_agents.sql`)
- **Environment Prefixes**: Use environment-specific prefixes where appropriate
- **Data Types**: Include data type in filename (e.g., `test_agents.sql`, `demo_scenarios.sql`)
- **Utilities**: Use descriptive names for utility scripts

### 3. Implementation
- **Idempotent Scripts**: Ensure seed scripts can be run multiple times safely
- **Data Validation**: Validate seed data before insertion
- **Error Handling**: Implement proper error handling and rollback
- **Performance**: Optimize seed scripts for fast execution
- **Documentation**: Document seed data purpose and relationships

### 4. Documentation
- **Seed Documentation**: Document the purpose and content of each seed file
- **Data Relationships**: Document relationships between seeded entities
- **Environment Setup**: Document environment-specific seeding procedures
- **Troubleshooting**: Provide troubleshooting guides for seeding issues

## Best Practices

### Seed Script Design
```python
# seed_runner.py - Main seeding script runner
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import json

logger = logging.getLogger(__name__)

class SeedRunner:
    def __init__(self, db_path: str, seeds_dir: str):
        self.db_path = db_path
        self.seeds_dir = Path(seeds_dir)
        self.executed_seeds = set()
    
    def run_seeds(self, environment: str = "development") -> bool:
        """Run all seeds for the specified environment."""
        try:
            env_dir = self.seeds_dir / environment
            if not env_dir.exists():
                logger.error(f"Environment directory not found: {env_dir}")
                return False
            
            # Get all seed files in order
            seed_files = sorted(env_dir.glob("*.sql"))
            
            logger.info(f"Running {len(seed_files)} seed files for {environment}")
            
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                
                for seed_file in seed_files:
                    if self._run_seed_file(conn, seed_file):
                        self.executed_seeds.add(seed_file.name)
                        logger.info(f"✅ Executed seed: {seed_file.name}")
                    else:
                        logger.error(f"❌ Failed to execute seed: {seed_file.name}")
                        return False
                
                conn.commit()
            
            logger.info(f"Successfully executed {len(seed_files)} seed files")
            return True
            
        except Exception as e:
            logger.error(f"Seed execution failed: {e}")
            return False
    
    def _run_seed_file(self, conn: sqlite3.Connection, seed_file: Path) -> bool:
        """Execute a single seed file."""
        try:
            with open(seed_file, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    conn.execute(statement)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing {seed_file}: {e}")
            return False
    
    def clear_seeds(self, environment: str = "development") -> bool:
        """Clear all seeded data for the environment."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Disable foreign key constraints for cleanup
                conn.execute("PRAGMA foreign_keys = OFF")
                
                # Clear tables in reverse dependency order
                cleanup_order = [
                    "cost_tracking",
                    "analytics_data", 
                    "conversation_messages",
                    "conversations",
                    "tasks",
                    "agents"
                ]
                
                for table in cleanup_order:
                    conn.execute(f"DELETE FROM {table} WHERE created_by = 'seed_script'")
                
                conn.commit()
                conn.execute("PRAGMA foreign_keys = ON")
            
            logger.info(f"Cleared seed data for {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear seed data: {e}")
            return False
```

### Security
- **Data Sanitization**: Sanitize all seed data to prevent injection attacks
- **Access Control**: Implement proper access controls for seed scripts
- **Sensitive Data**: Avoid including real sensitive data in seeds
- **Environment Isolation**: Ensure production seeds don't contain test data

### Performance
- **Batch Inserts**: Use batch inserts for large datasets
- **Index Management**: Disable indexes during bulk inserts if needed
- **Transaction Management**: Use transactions for atomic seed operations
- **Memory Management**: Manage memory usage for large seed datasets

### Testing
```python
import pytest
import tempfile
from pathlib import Path
from database.seeds.seed_runner import SeedRunner

@pytest.fixture
def temp_database():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_db_path = temp_file.name
    
    # Initialize database schema
    # ... schema initialization ...
    
    yield temp_db_path
    
    # Cleanup
    Path(temp_db_path).unlink(missing_ok=True)

def test_development_seeds(temp_database):
    """Test development environment seeding."""
    seed_runner = SeedRunner(temp_database, "database/seeds")
    
    # Run development seeds
    result = seed_runner.run_seeds("development")
    assert result is True
    
    # Verify seeded data
    with sqlite3.connect(temp_database) as conn:
        # Check agents were seeded
        agent_count = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
        assert agent_count > 0
        
        # Check tasks were seeded
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        assert task_count > 0

def test_seed_idempotency(temp_database):
    """Test that seeds can be run multiple times safely."""
    seed_runner = SeedRunner(temp_database, "database/seeds")
    
    # Run seeds twice
    result1 = seed_runner.run_seeds("testing")
    result2 = seed_runner.run_seeds("testing")
    
    assert result1 is True
    assert result2 is True
    
    # Verify no duplicate data
    with sqlite3.connect(temp_database) as conn:
        # Check for duplicate agents
        duplicate_agents = conn.execute("""
            SELECT name, COUNT(*) 
            FROM agents 
            GROUP BY name 
            HAVING COUNT(*) > 1
        """).fetchall()
        assert len(duplicate_agents) == 0
```

### Data Validation
- **Referential Integrity**: Ensure all foreign key references are valid
- **Data Consistency**: Validate data consistency across related tables
- **Business Rules**: Validate business rule compliance in seed data
- **Format Validation**: Validate data formats and constraints

## Examples

### Development Agent Seeds
```sql
-- development/001_initial_agents.sql
-- Initial agent configurations for development environment

-- Clear existing seed data (idempotent)
DELETE FROM agents WHERE created_by = 'seed_script';

-- Director Agent - Orchestrates and manages other agents
INSERT INTO agents (
    id, name, type, description, config, capabilities, status, 
    created_by, created_at, updated_at
) VALUES (
    'agent_director_001',
    'Main Director',
    'director',
    'Primary director agent responsible for task orchestration and agent coordination',
    json('{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2000, "system_prompt": "You are a director agent responsible for coordinating tasks and managing other agents."}'),
    json('["task_orchestration", "agent_management", "workflow_coordination", "decision_making"]'),
    'active',
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Communication Agent - Handles external communications
INSERT INTO agents (
    id, name, type, description, config, capabilities, status,
    created_by, created_at, updated_at
) VALUES (
    'agent_comm_001',
    'Communication Specialist',
    'specialist',
    'Specialized agent for handling email communications and external interactions',
    json('{"model": "gpt-3.5-turbo", "temperature": 0.5, "max_tokens": 1500, "system_prompt": "You are a communication specialist focused on clear, professional correspondence."}'),
    json('["email_composition", "communication_analysis", "tone_adjustment", "language_translation"]'),
    'active',
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Analytics Agent - Processes data and generates insights
INSERT INTO agents (
    id, name, type, description, config, capabilities, status,
    created_by, created_at, updated_at
) VALUES (
    'agent_analytics_001',
    'Data Analytics Specialist',
    'specialist',
    'Specialized agent for data analysis, reporting, and insight generation',
    json('{"model": "gpt-4", "temperature": 0.3, "max_tokens": 2500, "system_prompt": "You are a data analytics specialist focused on extracting insights from data."}'),
    json('["data_analysis", "report_generation", "statistical_analysis", "visualization_recommendations"]'),
    'active',
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Worker Agents - General purpose task execution
INSERT INTO agents (
    id, name, type, description, config, capabilities, status,
    created_by, created_at, updated_at
) VALUES 
(
    'agent_worker_001',
    'General Worker Alpha',
    'worker',
    'General purpose worker agent for task execution',
    json('{"model": "gpt-3.5-turbo", "temperature": 0.6, "max_tokens": 1000}'),
    json('["text_processing", "data_extraction", "content_generation", "task_execution"]'),
    'active',
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'agent_worker_002',
    'General Worker Beta',
    'worker',
    'General purpose worker agent for task execution',
    json('{"model": "gpt-3.5-turbo", "temperature": 0.6, "max_tokens": 1000}'),
    json('["text_processing", "data_extraction", "content_generation", "task_execution"]'),
    'active',
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### Sample Task Seeds
```sql
-- development/002_sample_tasks.sql
-- Sample task data for development environment

-- Clear existing seed data
DELETE FROM tasks WHERE created_by = 'seed_script';

-- High priority communication task
INSERT INTO tasks (
    id, title, description, category, priority, status,
    assigned_agent_id, instructions, estimated_duration,
    created_by, created_at, updated_at
) VALUES (
    'task_001',
    'Draft Welcome Email Template',
    'Create a professional welcome email template for new users',
    'communication',
    1,
    'pending',
    'agent_comm_001',
    'Create a warm, professional welcome email template that includes: company introduction, key features overview, getting started steps, and contact information. Tone should be friendly but professional.',
    1800, -- 30 minutes
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Analytics task
INSERT INTO tasks (
    id, title, description, category, priority, status,
    assigned_agent_id, instructions, estimated_duration,
    created_by, created_at, updated_at
) VALUES (
    'task_002',
    'Analyze User Engagement Metrics',
    'Generate insights from user engagement data',
    'analysis',
    2,
    'pending',
    'agent_analytics_001',
    'Analyze the provided user engagement metrics and generate a comprehensive report including: key trends, user behavior patterns, recommendations for improvement, and actionable insights.',
    3600, -- 60 minutes
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- General processing tasks
INSERT INTO tasks (
    id, title, description, category, priority, status,
    assigned_agent_id, instructions, estimated_duration,
    created_by, created_at, updated_at
) VALUES 
(
    'task_003',
    'Process Customer Feedback',
    'Categorize and summarize customer feedback submissions',
    'processing',
    3,
    'pending',
    'agent_worker_001',
    'Review customer feedback submissions and categorize them by type (feature request, bug report, general feedback). Provide a summary of common themes and priority issues.',
    2400, -- 40 minutes
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
),
(
    'task_004',
    'Generate Product Documentation',
    'Create user-friendly documentation for new features',
    'general',
    3,
    'pending',
    'agent_worker_002',
    'Create clear, user-friendly documentation for the new dashboard features. Include step-by-step instructions, screenshots placeholders, and troubleshooting tips.',
    4800, -- 80 minutes
    'seed_script',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Completed task example
INSERT INTO tasks (
    id, title, description, category, priority, status,
    assigned_agent_id, instructions, estimated_duration, actual_duration,
    result, assigned_at, started_at, completed_at,
    created_by, created_at, updated_at
) VALUES (
    'task_005',
    'System Health Check Report',
    'Generate daily system health check report',
    'analysis',
    2,
    'completed',
    'agent_analytics_001',
    'Generate a comprehensive system health check report including: server status, database performance, error rates, and recommendations.',
    1800, -- 30 minutes estimated
    1650, -- 27.5 minutes actual
    json('{"status": "healthy", "uptime": "99.9%", "errors": 2, "recommendations": ["Monitor disk space", "Update security patches"]}'),
    datetime('now', '-2 hours'),
    datetime('now', '-1.5 hours'),
    datetime('now', '-1 hour'),
    'seed_script',
    datetime('now', '-2 hours'),
    CURRENT_TIMESTAMP
);
```

### Data Generation Utility
```python
# utilities/data_generator.py - Synthetic data generation utility
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

class SyntheticDataGenerator:
    def __init__(self):
        self.agent_types = ['director', 'worker', 'specialist']
        self.task_categories = ['general', 'analysis', 'communication', 'processing']
        self.task_statuses = ['pending', 'assigned', 'in_progress', 'completed', 'failed']
        self.priorities = [1, 2, 3, 4, 5]
    
    def generate_agents(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic agent data."""
        agents = []
        
        for i in range(count):
            agent = {
                'id': f'synthetic_agent_{uuid.uuid4().hex[:8]}',
                'name': f'Synthetic Agent {i+1}',
                'type': random.choice(self.agent_types),
                'description': f'Synthetically generated agent for testing purposes',
                'config': json.dumps({
                    'model': random.choice(['gpt-3.5-turbo', 'gpt-4']),
                    'temperature': round(random.uniform(0.1, 1.0), 2),
                    'max_tokens': random.choice([1000, 1500, 2000, 2500])
                }),
                'capabilities': json.dumps([
                    f'capability_{j}' for j in range(random.randint(2, 6))
                ]),
                'status': random.choice(['active', 'inactive']),
                'performance_score': round(random.uniform(0.5, 1.0), 3),
                'created_by': 'synthetic_generator',
                'created_at': self._random_timestamp(days_back=30)
            }
            agents.append(agent)
        
        return agents
    
    def generate_tasks(self, count: int, agent_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate synthetic task data."""
        tasks = []
        
        for i in range(count):
            created_at = self._random_timestamp(days_back=14)
            status = random.choice(self.task_statuses)
            
            task = {
                'id': f'synthetic_task_{uuid.uuid4().hex[:8]}',
                'title': f'Synthetic Task {i+1}',
                'description': f'Synthetically generated task for testing and development',
                'category': random.choice(self.task_categories),
                'priority': random.choice(self.priorities),
                'status': status,
                'assigned_agent_id': random.choice(agent_ids) if agent_ids else None,
                'estimated_duration': random.randint(300, 7200),  # 5 minutes to 2 hours
                'created_by': 'synthetic_generator',
                'created_at': created_at
            }
            
            # Add completion data for completed tasks
            if status == 'completed':
                task['actual_duration'] = random.randint(
                    int(task['estimated_duration'] * 0.7),
                    int(task['estimated_duration'] * 1.3)
                )
                task['completed_at'] = created_at + timedelta(
                    seconds=task['actual_duration']
                )
                task['result'] = json.dumps({
                    'success': True,
                    'output': f'Completed synthetic task {i+1}'
                })
            
            tasks.append(task)
        
        return tasks
    
    def _random_timestamp(self, days_back: int) -> str:
        """Generate random timestamp within the last N days."""
        start_date = datetime.now() - timedelta(days=days_back)
        random_date = start_date + timedelta(
            seconds=random.randint(0, int(timedelta(days=days_back).total_seconds()))
        )
        return random_date.isoformat()
    
    def export_to_sql(self, data: List[Dict[str, Any]], table_name: str) -> str:
        """Export generated data to SQL INSERT statements."""
        if not data:
            return ""
        
        # Get column names from first record
        columns = list(data[0].keys())
        column_list = ', '.join(columns)
        
        sql_statements = [f"-- Generated synthetic data for {table_name}"]
        sql_statements.append(f"DELETE FROM {table_name} WHERE created_by = 'synthetic_generator';")
        sql_statements.append("")
        
        for record in data:
            values = []
            for column in columns:
                value = record[column]
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    # Escape single quotes
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                else:
                    values.append(str(value))
            
            values_list = ', '.join(values)
            sql_statements.append(
                f"INSERT INTO {table_name} ({column_list}) VALUES ({values_list});"
            )
        
        return '\n'.join(sql_statements)
```

## Related Documentation

- [Database Schema](../schemas/README.md) - Database schema documentation
- [Migration Procedures](../migrations/README.md) - Database migration guide
- [Test Data Management](../../docs/development/test_data.md) - Test data management guide
- [Development Setup](../../docs/development/getting_started.md) - Development environment setup
- [Data Import/Export](../../docs/development/data_import_export.md) - Data import and export procedures
- [Environment Configuration](../../config/README.md) - Environment configuration guide
