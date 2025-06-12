# Source Code Directory

## Purpose
Contains the complete source code for the SwarmDirector application, organized as a proper Python package following best practices for maintainability, testability, and scalability. This directory houses the core implementation of the three-tier hierarchical AI agent management system.

## Structure
```
src/
├── __init__.py                   # Package marker (empty)
└── swarm_director/              # Main application package
    ├── __init__.py              # Package initialization and version info
    ├── app.py                   # Flask application factory and routes
    ├── config.py                # Configuration management classes
    ├── agents/                  # AI agent implementations
    │   ├── __init__.py          # Agent package exports
    │   ├── base_agent.py        # Abstract base agent class
    │   ├── director.py          # Director agent (task routing)
    │   ├── supervisor_agent.py  # Supervisor agent implementation
    │   ├── worker_agent.py      # Worker agent implementation
    │   ├── communications_dept.py # Communications department agent
    │   ├── email_agent.py       # Email handling agent
    │   ├── draft_review_agent.py # Content review agent
    │   └── review_logic.py      # Review logic utilities
    ├── models/                  # Database models (SQLAlchemy)
    │   ├── __init__.py          # Model package exports
    │   ├── base.py              # Base model class with common functionality
    │   ├── agent.py             # Agent database model
    │   ├── task.py              # Task database model
    │   ├── conversation.py      # Conversation and message models
    │   ├── draft.py             # Draft content model
    │   ├── email_message.py     # Email message model
    │   └── agent_log.py         # Agent activity logging model
    ├── utils/                   # Utility functions and helpers
    │   ├── __init__.py          # Utility package exports
    │   ├── database.py          # Database connection and utilities
    │   ├── logging.py           # Logging configuration
    │   ├── migrations.py        # Database migration utilities
    │   ├── autogen_helpers.py   # AutoGen framework integration
    │   ├── autogen_integration.py # Advanced AutoGen integration
    │   ├── autogen_config.py    # AutoGen configuration templates
    │   ├── conversation_analytics.py # Conversation analysis tools
    │   ├── error_handler.py     # Error handling utilities
    │   ├── rate_limiter.py      # API rate limiting
    │   ├── response_formatter.py # Response formatting utilities
    │   ├── validation.py        # Input validation utilities
    │   └── db_cli.py            # Database CLI commands
    └── web/                     # Web interface components
        ├── __init__.py          # Web package initialization
        ├── static/              # Static assets (CSS, JS, images)
        └── templates/           # Jinja2 HTML templates
            └── demo/            # Demo interface templates
```

## Guidelines

### 1. Organization
- **Package Structure**: Follow Python packaging conventions with proper `__init__.py` files
- **Separation of Concerns**: Keep agents, models, utilities, and web components in separate packages
- **Import Management**: Use relative imports within packages, absolute imports from outside
- **Circular Dependencies**: Avoid circular imports by careful dependency design
- **Module Size**: Keep modules focused and under 500 lines when possible

### 2. Naming
- **Packages**: Use lowercase with underscores (snake_case)
- **Modules**: Use descriptive names indicating functionality (e.g., `base_agent.py`)
- **Classes**: Use PascalCase (e.g., `DirectorAgent`, `BaseModel`)
- **Functions**: Use snake_case (e.g., `execute_task`, `can_handle_task`)
- **Constants**: Use UPPER_CASE (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)

### 3. Implementation
- **Abstract Base Classes**: Use ABC for defining agent and model interfaces
- **Type Hints**: Include comprehensive type annotations for all public APIs
- **Docstrings**: Use Google-style docstrings for all classes and functions
- **Error Handling**: Implement comprehensive error handling with proper exception types
- **Configuration**: Use dependency injection for configuration management

### 4. Documentation
- **Module Docstrings**: Include purpose and usage examples at module level
- **Class Docstrings**: Document class purpose, attributes, and usage patterns
- **Method Docstrings**: Include parameters, return values, and exceptions
- **Inline Comments**: Use sparingly for complex logic explanation

## Best Practices

### 1. Error Handling
- **Custom Exceptions**: Define domain-specific exception classes in each package
- **Graceful Degradation**: Handle optional dependencies (AutoGen) with try/except blocks
- **Logging Integration**: Log errors with appropriate levels and context
- **User-Friendly Messages**: Provide actionable error messages for common failures
- **Exception Chaining**: Use `raise ... from ...` to preserve error context

### 2. Security
- **Input Validation**: Validate all external inputs using dedicated validation utilities
- **SQL Injection Prevention**: Use SQLAlchemy ORM and parameterized queries
- **Sensitive Data**: Never log or expose sensitive configuration data
- **Access Control**: Implement proper authorization checks in agent operations
- **Dependency Security**: Regularly audit and update dependencies

### 3. Performance
- **Database Optimization**: Use efficient queries and proper indexing
- **Memory Management**: Implement proper cleanup in long-running operations
- **Caching**: Cache expensive computations and database queries
- **Async Operations**: Use async/await for I/O-bound operations
- **Resource Pooling**: Use connection pooling for database and external services

### 4. Testing
- **Unit Tests**: Test each module in isolation with comprehensive coverage
- **Integration Tests**: Test interactions between components
- **Mock Dependencies**: Use mocks for external services and databases
- **Test Data**: Use factories and fixtures for consistent test data
- **Performance Tests**: Include benchmarks for critical operations

### 5. Documentation
- **API Documentation**: Generate API docs from docstrings using Sphinx
- **Code Examples**: Include working examples in docstrings
- **Architecture Documentation**: Document design decisions and patterns
- **Migration Guides**: Document breaking changes and upgrade paths

## Example

### Creating a New Agent Implementation

```python
"""
Example: Creating a new specialized agent
Demonstrates proper agent implementation following SwarmDirector patterns
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Any
from ..models.agent import Agent, AgentStatus, AgentType
from ..models.task import Task, TaskStatus
from ..utils.logging import log_agent_action
from ..utils.error_handler import handle_agent_error
from .base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    """
    Specialized agent for research and information gathering tasks
    
    This agent handles tasks that require web research, data analysis,
    and information synthesis capabilities.
    
    Attributes:
        research_capabilities: List of research methods supported
        max_sources: Maximum number of sources to consult
        confidence_threshold: Minimum confidence level for results
    """
    
    def __init__(self, db_agent: Agent):
        """Initialize the research agent with database model"""
        super().__init__(db_agent)
        self.research_capabilities = self.capabilities.get('research_methods', [])
        self.max_sources = self.capabilities.get('max_sources', 10)
        self.confidence_threshold = self.capabilities.get('confidence_threshold', 0.8)
    
    def can_handle_task(self, task: Task) -> bool:
        """
        Check if this agent can handle the given research task
        
        Args:
            task: Task to evaluate
            
        Returns:
            bool: True if agent can handle the task
        """
        # Check task type
        if task.task_type not in ['research', 'analysis', 'information_gathering']:
            return False
        
        # Check required capabilities
        required_methods = task.input_data.get('research_methods', [])
        if required_methods and not all(method in self.research_capabilities for method in required_methods):
            return False
        
        # Check agent availability
        return self.is_available()
    
    @handle_agent_error
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a research task
        
        Args:
            task: Research task to execute
            
        Returns:
            Dict containing research results and metadata
            
        Raises:
            ValueError: If task parameters are invalid
            RuntimeError: If research operation fails
        """
        log_agent_action(self.name, f"Starting research task: {task.title}")
        
        try:
            # Update agent status
            self.update_status(AgentStatus.ACTIVE)
            
            # Extract task parameters
            query = task.input_data.get('query')
            if not query:
                raise ValueError("Research query is required")
            
            sources_limit = min(
                task.input_data.get('max_sources', self.max_sources),
                self.max_sources
            )
            
            # Perform research
            research_results = self._conduct_research(query, sources_limit)
            
            # Analyze and synthesize results
            analysis = self._analyze_results(research_results)
            
            # Validate confidence level
            if analysis['confidence'] < self.confidence_threshold:
                log_agent_action(self.name, f"Low confidence result: {analysis['confidence']}")
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.output_data = {
                'research_results': research_results,
                'analysis': analysis,
                'sources_consulted': len(research_results),
                'confidence_score': analysis['confidence'],
                'completion_time': task.actual_duration
            }
            task.save()
            
            log_agent_action(self.name, f"Research task completed: {task.title}")
            
            return {
                'status': 'completed',
                'task_id': task.id,
                'results': task.output_data,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            # Handle errors and update task status
            task.status = TaskStatus.FAILED
            task.error_details = str(e)
            task.save()
            
            log_agent_action(self.name, f"Research task failed: {e}")
            raise
            
        finally:
            # Reset agent status
            self.update_status(AgentStatus.IDLE)
    
    def _conduct_research(self, query: str, max_sources: int) -> List[Dict[str, Any]]:
        """
        Conduct research using available methods
        
        Args:
            query: Research query
            max_sources: Maximum number of sources to consult
            
        Returns:
            List of research results with source information
        """
        # Implementation would include actual research logic
        # This is a simplified example
        results = []
        
        for method in self.research_capabilities:
            if len(results) >= max_sources:
                break
                
            method_results = self._research_with_method(method, query)
            results.extend(method_results)
        
        return results[:max_sources]
    
    def _research_with_method(self, method: str, query: str) -> List[Dict[str, Any]]:
        """Research using a specific method"""
        # Placeholder for actual research implementation
        return [
            {
                'method': method,
                'query': query,
                'source': f"Source from {method}",
                'content': f"Research content for {query}",
                'relevance_score': 0.85,
                'timestamp': '2023-12-01T10:00:00Z'
            }
        ]
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze and synthesize research results"""
        if not results:
            return {'confidence': 0.0, 'summary': 'No results found'}
        
        # Calculate confidence based on source quality and agreement
        confidence = sum(r.get('relevance_score', 0) for r in results) / len(results)
        
        # Generate summary
        summary = f"Research completed with {len(results)} sources. Average relevance: {confidence:.2f}"
        
        return {
            'confidence': confidence,
            'summary': summary,
            'source_count': len(results),
            'methods_used': list(set(r['method'] for r in results))
        }

# Agent factory function
def create_research_agent(name: str, capabilities: Dict[str, Any]) -> ResearchAgent:
    """
    Factory function to create a research agent
    
    Args:
        name: Agent name
        capabilities: Agent capabilities configuration
        
    Returns:
        Configured ResearchAgent instance
    """
    # Create database model
    db_agent = Agent(
        name=name,
        description="Specialized agent for research and information gathering",
        agent_type=AgentType.WORKER,
        capabilities=capabilities
    )
    db_agent.save()
    
    # Create and return agent instance
    return ResearchAgent(db_agent)
```

## Related Documentation
- [Main Application Package](swarm_director/DIRECTORY.md) - Core application structure
- [Agent Implementation Guide](../docs/api/agents.md) - Agent development patterns
- [Model Design Guide](../docs/architecture/database_design.md) - Database model patterns
- [Utility Functions Guide](../docs/development/coding_standards.md) - Utility development standards
- [Web Interface Guide](../docs/api/README.md) - Web component development
