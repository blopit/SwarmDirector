---
task_id: task_009
subtask_id: null
title: Implement End-to-End Email Workflow
status: pending
priority: medium
parent_task: null
dependencies: ['task_005', 'task_006', 'task_007', 'task_008']
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Integrate all components to create the complete workflow from DirectorAgent through CommunicationsDept to EmailAgent.

## 📋 Metadata
- **ID**: task_009
- **Title**: Implement End-to-End Email Workflow
- **Status**: pending
- **Priority**: medium
- **Parent Task**: null
- **Dependencies**: ['task_005', 'task_006', 'task_007', 'task_008']
- **Subtasks**: 4
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints
- **In Scope**: Complete end-to-end email workflow orchestration with state management, error recovery, transaction integrity, performance monitoring, and comprehensive logging
- **Out of Scope**: Real-time collaboration features, email scheduling, bulk email campaigns, advanced analytics dashboards, multi-language support
- **Assumptions**: Python 3.8+, all dependent agents implemented (DirectorAgent, CommunicationsDept, DraftReviewAgent, EmailAgent), database available, basic workflow orchestration knowledge
- **Constraints**: Must handle 50+ concurrent workflows, complete within 5 minutes per email, maintain ACID properties, support rollback on failures

---

## 🔍 1. Detailed Description

The End-to-End Email Workflow orchestrates the complete process from task submission to email delivery. It integrates DirectorAgent for task routing, CommunicationsDept for draft creation, DraftReviewAgent for content improvement, and EmailAgent for final delivery. The workflow includes comprehensive state management, error recovery, and performance monitoring to ensure reliable email generation and delivery.

### Workflow Stages:
1. **Task Reception**: Receive email task from API endpoint
2. **Director Routing**: Route task to CommunicationsDept via DirectorAgent
3. **Draft Creation**: Generate initial email draft
4. **Review Process**: Multiple review agents improve draft quality
5. **Final Assembly**: Merge feedback and create final draft
6. **Email Delivery**: Send email via EmailAgent
7. **Status Tracking**: Monitor and log entire process

### Key Features:
- **State Management**: Track workflow progress through all stages
- **Error Recovery**: Automatic retry and fallback mechanisms
- **Transaction Integrity**: Ensure data consistency across failures
- **Performance Monitoring**: Real-time metrics and alerting
- **Concurrent Processing**: Handle multiple workflows simultaneously

## 📁 2. Reference Artifacts & Files

### Project Structure
```
workflows/
├── __init__.py
├── email_workflow.py       # Main workflow orchestrator
├── workflow_state.py       # State management
├── workflow_monitor.py     # Performance monitoring
└── workflow_recovery.py    # Error recovery mechanisms

orchestration/
├── __init__.py
├── agent_coordinator.py    # Agent coordination logic
├── task_dispatcher.py      # Task distribution
└── result_aggregator.py    # Result collection

state/
├── __init__.py
├── workflow_tracker.py     # Workflow state tracking
├── transaction_manager.py  # Database transaction management
└── checkpoint_manager.py   # Workflow checkpoints

models/
├── workflow_instance.py    # Workflow instance model
├── workflow_step.py        # Individual step tracking
└── workflow_metrics.py     # Performance metrics model

tests/
├── test_email_workflow.py  # End-to-end workflow tests
├── test_state_management.py # State management tests
├── test_error_recovery.py  # Error recovery tests
└── fixtures/               # Test data and mocks
    ├── sample_workflows.py
    └── mock_agents.py
```

### Required Files
- **workflows/email_workflow.py**: Main workflow orchestrator
- **orchestration/agent_coordinator.py**: Agent coordination logic
- **state/workflow_tracker.py**: State management system
- **state/transaction_manager.py**: Database transaction handling
- **tests/test_email_workflow.py**: Comprehensive test suite

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 Email Workflow Orchestrator (workflows/email_workflow.py)
```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field

from orchestration.agent_coordinator import AgentCoordinator
from state.workflow_tracker import WorkflowTracker
from state.transaction_manager import TransactionManager
from workflows.workflow_monitor import WorkflowMonitor
from workflows.workflow_recovery import WorkflowRecovery
from models.workflow_instance import WorkflowInstance

class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    PENDING = "pending"
    ROUTING = "routing"
    DRAFTING = "drafting"
    REVIEWING = "reviewing"
    FINALIZING = "finalizing"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowResult:
    """Workflow execution result."""
    workflow_id: str
    status: WorkflowStatus
    email_id: Optional[str] = None
    final_draft: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    steps_completed: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class EmailWorkflowOrchestrator:
    """
    Orchestrates the complete end-to-end email workflow.
    Coordinates between DirectorAgent, CommunicationsDept, DraftReviewAgent, and EmailAgent.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the workflow orchestrator."""
        self.config = config or self._get_default_config()
        self.logger = self._setup_logging()

        # Initialize components
        self.agent_coordinator = AgentCoordinator(self.config)
        self.workflow_tracker = WorkflowTracker()
        self.transaction_manager = TransactionManager()
        self.monitor = WorkflowMonitor()
        self.recovery = WorkflowRecovery()

        # Workflow configuration
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.timeout_seconds = self.config.get('timeout_seconds', 300)  # 5 minutes
        self.checkpoint_interval = self.config.get('checkpoint_interval', 30)  # seconds

    def _get_default_config(self) -> Dict:
        """Get default configuration for workflow orchestrator."""
        return {
            'max_retry_attempts': 3,
            'timeout_seconds': 300,
            'checkpoint_interval': 30,
            'enable_monitoring': True,
            'enable_recovery': True,
            'parallel_reviews': True,
            'max_concurrent_workflows': 50
        }

    async def execute_email_workflow(self, task_data: Dict) -> WorkflowResult:
        """
        Execute the complete email workflow.

        Args:
            task_data: Task data containing email requirements

        Returns:
            WorkflowResult with execution details
        """
        workflow_id = self._generate_workflow_id()
        start_time = datetime.utcnow()

        try:
            # Initialize workflow tracking
            workflow_instance = await self._initialize_workflow(workflow_id, task_data)

            # Start monitoring
            if self.config.get('enable_monitoring'):
                self.monitor.start_workflow_monitoring(workflow_id)

            # Execute workflow steps
            result = await self._execute_workflow_steps(workflow_instance)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time

            # Update final status
            await self.workflow_tracker.update_status(workflow_id, result.status)

            self.logger.info(f"Workflow {workflow_id} completed with status: {result.status}")
            return result

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {str(e)}")

            # Attempt recovery if enabled
            if self.config.get('enable_recovery'):
                recovery_result = await self.recovery.attempt_recovery(workflow_id, str(e))
                if recovery_result.success:
                    return recovery_result.workflow_result

            # Return failure result
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                error_message=str(e),
                execution_time=execution_time
            )
        finally:
            # Stop monitoring
            if self.config.get('enable_monitoring'):
                self.monitor.stop_workflow_monitoring(workflow_id)

    async def _execute_workflow_steps(self, workflow_instance: WorkflowInstance) -> WorkflowResult:
        """Execute all workflow steps in sequence."""
        workflow_id = workflow_instance.workflow_id
        task_data = workflow_instance.task_data

        try:
            # Step 1: Route task through DirectorAgent
            await self._update_workflow_status(workflow_id, WorkflowStatus.ROUTING)
            routing_result = await self._route_task(task_data)
            await self._create_checkpoint(workflow_id, "routing_completed", routing_result)

            # Step 2: Generate initial draft via CommunicationsDept
            await self._update_workflow_status(workflow_id, WorkflowStatus.DRAFTING)
            draft_result = await self._generate_draft(routing_result)
            await self._create_checkpoint(workflow_id, "draft_created", draft_result)

            # Step 3: Review draft with DraftReviewAgents
            await self._update_workflow_status(workflow_id, WorkflowStatus.REVIEWING)
            review_result = await self._review_draft(draft_result)
            await self._create_checkpoint(workflow_id, "review_completed", review_result)

            # Step 4: Finalize draft with improvements
            await self._update_workflow_status(workflow_id, WorkflowStatus.FINALIZING)
            final_draft = await self._finalize_draft(draft_result, review_result)
            await self._create_checkpoint(workflow_id, "draft_finalized", final_draft)

            # Step 5: Send email via EmailAgent
            await self._update_workflow_status(workflow_id, WorkflowStatus.SENDING)
            email_result = await self._send_email(final_draft, task_data)
            await self._create_checkpoint(workflow_id, "email_sent", email_result)

            # Step 6: Complete workflow
            await self._update_workflow_status(workflow_id, WorkflowStatus.COMPLETED)

            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                email_id=email_result.get('email_id'),
                final_draft=final_draft.get('content'),
                steps_completed=[
                    "routing_completed",
                    "draft_created",
                    "review_completed",
                    "draft_finalized",
                    "email_sent"
                ],
                metrics=await self._collect_workflow_metrics(workflow_id)
            )

        except Exception as e:
            await self._update_workflow_status(workflow_id, WorkflowStatus.FAILED)
            raise

    async def _route_task(self, task_data: Dict) -> Dict:
        """Route task through DirectorAgent."""
        try:
            director_agent = await self.agent_coordinator.get_director_agent()

            routing_request = {
                "task_type": "email_generation",
                "task_data": task_data,
                "target_agent": "CommunicationsDept"
            }

            result = await director_agent.route_task(routing_request)

            if not result.get('success'):
                raise Exception(f"Task routing failed: {result.get('error')}")

            return result

        except Exception as e:
            self.logger.error(f"Task routing failed: {str(e)}")
            raise

    async def _generate_draft(self, routing_result: Dict) -> Dict:
        """Generate initial draft via CommunicationsDept."""
        try:
            communications_agent = await self.agent_coordinator.get_communications_agent()

            draft_request = {
                "task_data": routing_result.get('task_data'),
                "routing_context": routing_result.get('context'),
                "requirements": routing_result.get('requirements', {})
            }

            result = await communications_agent.create_draft(draft_request)

            if not result.get('success'):
                raise Exception(f"Draft generation failed: {result.get('error')}")

            return result

        except Exception as e:
            self.logger.error(f"Draft generation failed: {str(e)}")
            raise

    async def _review_draft(self, draft_result: Dict) -> Dict:
        """Review draft with multiple DraftReviewAgents."""
        try:
            review_agents = await self.agent_coordinator.get_review_agents()
            draft_content = draft_result.get('draft_content')

            if self.config.get('parallel_reviews', True):
                # Execute reviews in parallel
                review_tasks = [
                    agent.review_draft(draft_content, review_type)
                    for agent, review_type in review_agents
                ]
                review_results = await asyncio.gather(*review_tasks)
            else:
                # Execute reviews sequentially
                review_results = []
                for agent, review_type in review_agents:
                    result = await agent.review_draft(draft_content, review_type)
                    review_results.append(result)

            # Aggregate review results
            aggregated_reviews = self._aggregate_review_results(review_results)

            return {
                "success": True,
                "reviews": review_results,
                "aggregated_feedback": aggregated_reviews,
                "quality_score": self._calculate_overall_quality_score(review_results)
            }

        except Exception as e:
            self.logger.error(f"Draft review failed: {str(e)}")
            raise

    async def _finalize_draft(self, draft_result: Dict, review_result: Dict) -> Dict:
        """Finalize draft by applying review feedback."""
        try:
            communications_agent = await self.agent_coordinator.get_communications_agent()

            finalization_request = {
                "original_draft": draft_result.get('draft_content'),
                "review_feedback": review_result.get('aggregated_feedback'),
                "quality_requirements": {
                    "min_quality_score": 80,
                    "required_improvements": review_result.get('critical_issues', [])
                }
            }

            result = await communications_agent.finalize_draft(finalization_request)

            if not result.get('success'):
                raise Exception(f"Draft finalization failed: {result.get('error')}")

            return result

        except Exception as e:
            self.logger.error(f"Draft finalization failed: {str(e)}")
            raise

    async def _send_email(self, final_draft: Dict, task_data: Dict) -> Dict:
        """Send email via EmailAgent."""
        try:
            email_agent = await self.agent_coordinator.get_email_agent()

            email_request = {
                "to": task_data.get('recipient'),
                "subject": final_draft.get('subject'),
                "body": final_draft.get('content'),
                "metadata": {
                    "workflow_id": final_draft.get('workflow_id'),
                    "quality_score": final_draft.get('quality_score'),
                    "generation_time": final_draft.get('generation_time')
                }
            }

            result = await email_agent.send_email(**email_request)

            if result.get('status') != 'sent':
                raise Exception(f"Email sending failed: {result.get('message')}")

            return result

        except Exception as e:
            self.logger.error(f"Email sending failed: {str(e)}")
            raise
```

### 3.2 Agent Coordinator (orchestration/agent_coordinator.py)
```python
import asyncio
from typing import Dict, List, Tuple, Optional
from agents.director import DirectorAgent
from agents.communications import CommunicationsDept
from agents.review import DraftReviewAgent
from agents.email import EmailAgent

class AgentCoordinator:
    """Coordinates interactions between different agents in the workflow."""

    def __init__(self, config: Dict):
        self.config = config
        self._agent_pool = {}
        self._agent_locks = {}

    async def get_director_agent(self) -> DirectorAgent:
        """Get or create DirectorAgent instance."""
        if 'director' not in self._agent_pool:
            self._agent_pool['director'] = DirectorAgent("WorkflowDirector")
            self._agent_locks['director'] = asyncio.Lock()

        return self._agent_pool['director']

    async def get_communications_agent(self) -> CommunicationsDept:
        """Get or create CommunicationsDept instance."""
        if 'communications' not in self._agent_pool:
            self._agent_pool['communications'] = CommunicationsDept("WorkflowCommunications")
            self._agent_locks['communications'] = asyncio.Lock()

        return self._agent_pool['communications']

    async def get_review_agents(self) -> List[Tuple[DraftReviewAgent, str]]:
        """Get multiple review agents for parallel processing."""
        review_types = ['grammar', 'style', 'clarity', 'coherence']
        agents = []

        for review_type in review_types:
            agent_key = f'review_{review_type}'
            if agent_key not in self._agent_pool:
                self._agent_pool[agent_key] = DraftReviewAgent(f"Reviewer_{review_type}")
                self._agent_locks[agent_key] = asyncio.Lock()

            agents.append((self._agent_pool[agent_key], review_type))

        return agents

    async def get_email_agent(self) -> EmailAgent:
        """Get or create EmailAgent instance."""
        if 'email' not in self._agent_pool:
            self._agent_pool['email'] = EmailAgent("WorkflowEmailer")
            self._agent_locks['email'] = asyncio.Lock()

        return self._agent_pool['email']

    async def cleanup_agents(self):
        """Cleanup agent resources."""
        for agent_key, agent in self._agent_pool.items():
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()

        self._agent_pool.clear()
        self._agent_locks.clear()
```

---

## 🔌 4. API Endpoints

### 4.1 Workflow Management API
```python
from flask import Blueprint, request, jsonify
from workflows.email_workflow import EmailWorkflowOrchestrator
import asyncio

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/v1/workflow')

@workflow_bp.route('/email', methods=['POST'])
def start_email_workflow():
    """Start a new email workflow."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['recipient', 'subject', 'content_requirements']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Create workflow orchestrator
        orchestrator = EmailWorkflowOrchestrator()

        # Execute workflow asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                orchestrator.execute_email_workflow(data)
            )

            return jsonify({
                "workflow_id": result.workflow_id,
                "status": result.status.value,
                "email_id": result.email_id,
                "execution_time": result.execution_time,
                "steps_completed": result.steps_completed
            })

        finally:
            loop.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workflow_bp.route('/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """Get workflow execution status."""
    try:
        tracker = WorkflowTracker()
        status_info = tracker.get_workflow_status(workflow_id)

        if not status_info:
            return jsonify({"error": "Workflow not found"}), 404

        return jsonify(status_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@workflow_bp.route('/cancel/<workflow_id>', methods=['POST'])
def cancel_workflow(workflow_id):
    """Cancel a running workflow."""
    try:
        tracker = WorkflowTracker()
        result = tracker.cancel_workflow(workflow_id)

        return jsonify({
            "workflow_id": workflow_id,
            "cancelled": result.success,
            "message": result.message
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### 4.2 API Documentation
| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| POST | `/api/v1/workflow/email` | Start email workflow | Email task data | Workflow ID and status |
| GET | `/api/v1/workflow/status/<id>` | Get workflow status | None | Status and progress |
| POST | `/api/v1/workflow/cancel/<id>` | Cancel workflow | None | Cancellation result |
| GET | `/api/v1/workflow/metrics/<id>` | Get workflow metrics | None | Performance metrics |

---

## 📦 5. Dependencies

### 5.1 Required Packages
```txt
# Core async framework
asyncio==3.4.3

# Database and ORM
SQLAlchemy==2.0.23
alembic==1.12.1

# State management
redis==5.0.1
celery==5.3.4

# Monitoring and metrics
prometheus-client==0.19.0
structlog==23.2.0

# Workflow orchestration
prefect==2.14.0  # Optional: Advanced workflow engine
airflow==2.7.0   # Alternative: Apache Airflow

# Testing
pytest-asyncio==0.21.1
pytest-mock==3.12.0
aioresponses==0.7.4

# Utilities
python-dateutil==2.8.2
pydantic==2.5.0
```

### 5.2 Installation Commands
```bash
# Install core async dependencies
pip install asyncio==3.4.3

# Install database support
pip install SQLAlchemy==2.0.23 alembic==1.12.1

# Install state management
pip install redis==5.0.1 celery==5.3.4

# Install monitoring
pip install prometheus-client==0.19.0 structlog==23.2.0

# Install testing dependencies
pip install pytest-asyncio==0.21.1 pytest-mock==3.12.0 aioresponses==0.7.4

# Install utilities
pip install python-dateutil==2.8.2 pydantic==2.5.0
```

### 5.3 Environment Configuration
```bash
# Workflow Configuration
export WORKFLOW_MAX_CONCURRENT="50"
export WORKFLOW_TIMEOUT_SECONDS="300"
export WORKFLOW_RETRY_ATTEMPTS="3"

# State Management
export REDIS_URL="redis://localhost:6379/1"
export WORKFLOW_DB_URL="postgresql://user:pass@localhost/workflows"

# Monitoring
export PROMETHEUS_PORT="8000"
export WORKFLOW_LOG_LEVEL="INFO"

# Agent Configuration
export AGENT_POOL_SIZE="10"
export AGENT_TIMEOUT_SECONDS="60"
```

---

## 🛠️ 6. Implementation Plan

### Step 1: Project Setup and Structure
```bash
# Create directory structure
mkdir -p workflows orchestration state models tests/fixtures

# Create required files
touch workflows/__init__.py workflows/email_workflow.py workflows/workflow_monitor.py workflows/workflow_recovery.py
touch orchestration/__init__.py orchestration/agent_coordinator.py orchestration/task_dispatcher.py orchestration/result_aggregator.py
touch state/__init__.py state/workflow_tracker.py state/transaction_manager.py state/checkpoint_manager.py
touch models/workflow_instance.py models/workflow_step.py models/workflow_metrics.py
touch tests/test_email_workflow.py tests/test_state_management.py tests/test_error_recovery.py
```

### Step 2: State Management Implementation
```python
# state/workflow_tracker.py
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import redis
from sqlalchemy.orm import sessionmaker
from models.workflow_instance import WorkflowInstance

class WorkflowTracker:
    """Tracks workflow state and progress."""

    def __init__(self, redis_url: str = None, db_session = None):
        self.redis_client = redis.from_url(redis_url or "redis://localhost:6379/1")
        self.db_session = db_session
        self.lock_timeout = 300  # 5 minutes

    async def create_workflow(self, workflow_id: str, task_data: Dict) -> WorkflowInstance:
        """Create new workflow instance."""
        workflow = WorkflowInstance(
            workflow_id=workflow_id,
            task_data=task_data,
            status="pending",
            created_at=datetime.utcnow()
        )

        # Store in database
        if self.db_session:
            self.db_session.add(workflow)
            self.db_session.commit()

        # Store in Redis for fast access
        await self._store_workflow_state(workflow_id, workflow.to_dict())

        return workflow

    async def update_status(self, workflow_id: str, status: str, metadata: Dict = None):
        """Update workflow status."""
        workflow_data = await self._get_workflow_state(workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow_data['status'] = status
        workflow_data['updated_at'] = datetime.utcnow().isoformat()

        if metadata:
            workflow_data.setdefault('metadata', {}).update(metadata)

        await self._store_workflow_state(workflow_id, workflow_data)

    async def add_step(self, workflow_id: str, step_name: str, step_data: Dict):
        """Add completed step to workflow."""
        workflow_data = await self._get_workflow_state(workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")

        steps = workflow_data.setdefault('completed_steps', [])
        steps.append({
            'step_name': step_name,
            'completed_at': datetime.utcnow().isoformat(),
            'data': step_data
        })

        await self._store_workflow_state(workflow_id, workflow_data)

    async def _store_workflow_state(self, workflow_id: str, data: Dict):
        """Store workflow state in Redis."""
        key = f"workflow:{workflow_id}"
        await self.redis_client.setex(key, 3600, json.dumps(data, default=str))

    async def _get_workflow_state(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow state from Redis."""
        key = f"workflow:{workflow_id}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None

# state/transaction_manager.py
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Callable
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

class TransactionManager:
    """Manages database transactions across workflow steps."""

    def __init__(self, db_session_factory):
        self.session_factory = db_session_factory
        self.active_transactions = {}

    @asynccontextmanager
    async def transaction(self, workflow_id: str):
        """Create transactional context for workflow operations."""
        session = self.session_factory()
        transaction = session.begin()

        try:
            self.active_transactions[workflow_id] = {
                'session': session,
                'transaction': transaction
            }

            yield session

            # Commit if no exceptions
            transaction.commit()

        except Exception as e:
            # Rollback on any exception
            transaction.rollback()
            raise
        finally:
            # Cleanup
            session.close()
            self.active_transactions.pop(workflow_id, None)

    async def create_savepoint(self, workflow_id: str, savepoint_name: str):
        """Create savepoint within transaction."""
        if workflow_id not in self.active_transactions:
            raise ValueError(f"No active transaction for workflow {workflow_id}")

        session = self.active_transactions[workflow_id]['session']
        savepoint = session.begin_nested()

        self.active_transactions[workflow_id][f'savepoint_{savepoint_name}'] = savepoint
        return savepoint

    async def rollback_to_savepoint(self, workflow_id: str, savepoint_name: str):
        """Rollback to specific savepoint."""
        if workflow_id not in self.active_transactions:
            raise ValueError(f"No active transaction for workflow {workflow_id}")

        savepoint_key = f'savepoint_{savepoint_name}'
        if savepoint_key not in self.active_transactions[workflow_id]:
            raise ValueError(f"Savepoint {savepoint_name} not found")

        savepoint = self.active_transactions[workflow_id][savepoint_key]
        savepoint.rollback()
```

### Step 3: Workflow Monitoring
```python
# workflows/workflow_monitor.py
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Prometheus metrics
workflow_counter = Counter('workflows_total', 'Total workflows', ['status'])
workflow_duration = Histogram('workflow_duration_seconds', 'Workflow duration')
active_workflows = Gauge('active_workflows', 'Currently active workflows')

class WorkflowMonitor:
    """Monitors workflow performance and health."""

    def __init__(self):
        self.logger = structlog.get_logger()
        self.active_workflows = {}
        self.metrics_collection_interval = 30  # seconds

    def start_workflow_monitoring(self, workflow_id: str):
        """Start monitoring a workflow."""
        self.active_workflows[workflow_id] = {
            'start_time': time.time(),
            'last_heartbeat': time.time(),
            'step_times': {},
            'memory_usage': [],
            'error_count': 0
        }

        active_workflows.inc()
        self.logger.info("Workflow monitoring started", workflow_id=workflow_id)

    def stop_workflow_monitoring(self, workflow_id: str):
        """Stop monitoring a workflow."""
        if workflow_id in self.active_workflows:
            workflow_data = self.active_workflows.pop(workflow_id)
            duration = time.time() - workflow_data['start_time']

            workflow_duration.observe(duration)
            active_workflows.dec()

            self.logger.info("Workflow monitoring stopped",
                           workflow_id=workflow_id,
                           duration=duration)

    def record_step_completion(self, workflow_id: str, step_name: str, duration: float):
        """Record step completion time."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]['step_times'][step_name] = duration
            self.active_workflows[workflow_id]['last_heartbeat'] = time.time()

    def record_error(self, workflow_id: str, error_message: str):
        """Record workflow error."""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]['error_count'] += 1

        self.logger.error("Workflow error",
                         workflow_id=workflow_id,
                         error=error_message)

    async def collect_metrics(self) -> Dict:
        """Collect current workflow metrics."""
        current_time = time.time()
        metrics = {
            'active_workflow_count': len(self.active_workflows),
            'workflows_by_duration': {},
            'stuck_workflows': [],
            'error_rates': {}
        }

        for workflow_id, data in self.active_workflows.items():
            duration = current_time - data['start_time']
            last_activity = current_time - data['last_heartbeat']

            # Categorize by duration
            if duration < 60:
                category = 'under_1min'
            elif duration < 300:
                category = '1_to_5min'
            else:
                category = 'over_5min'

            metrics['workflows_by_duration'].setdefault(category, 0)
            metrics['workflows_by_duration'][category] += 1

            # Identify stuck workflows (no activity for 2 minutes)
            if last_activity > 120:
                metrics['stuck_workflows'].append({
                    'workflow_id': workflow_id,
                    'duration': duration,
                    'last_activity': last_activity
                })

        return metrics
```

### Step 4: Error Recovery Implementation
```python
# workflows/workflow_recovery.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from state.workflow_tracker import WorkflowTracker
from state.checkpoint_manager import CheckpointManager

@dataclass
class RecoveryResult:
    success: bool
    message: str
    workflow_result: Optional[Dict] = None
    recovery_actions: List[str] = None

class WorkflowRecovery:
    """Handles workflow error recovery and retry logic."""

    def __init__(self):
        self.tracker = WorkflowTracker()
        self.checkpoint_manager = CheckpointManager()
        self.max_retry_attempts = 3
        self.retry_delays = [30, 60, 120]  # seconds

    async def attempt_recovery(self, workflow_id: str, error_message: str) -> RecoveryResult:
        """Attempt to recover from workflow failure."""
        try:
            # Get workflow state
            workflow_data = await self.tracker._get_workflow_state(workflow_id)
            if not workflow_data:
                return RecoveryResult(
                    success=False,
                    message="Workflow data not found for recovery"
                )

            # Determine recovery strategy
            recovery_strategy = self._determine_recovery_strategy(workflow_data, error_message)

            # Execute recovery
            if recovery_strategy == 'retry_from_checkpoint':
                return await self._retry_from_checkpoint(workflow_id, workflow_data)
            elif recovery_strategy == 'retry_failed_step':
                return await self._retry_failed_step(workflow_id, workflow_data)
            elif recovery_strategy == 'fallback_execution':
                return await self._fallback_execution(workflow_id, workflow_data)
            else:
                return RecoveryResult(
                    success=False,
                    message=f"No recovery strategy available for error: {error_message}"
                )

        except Exception as e:
            return RecoveryResult(
                success=False,
                message=f"Recovery attempt failed: {str(e)}"
            )

    def _determine_recovery_strategy(self, workflow_data: Dict, error_message: str) -> str:
        """Determine the best recovery strategy based on error and workflow state."""
        error_lower = error_message.lower()

        # Network/timeout errors - retry from checkpoint
        if any(keyword in error_lower for keyword in ['timeout', 'connection', 'network']):
            return 'retry_from_checkpoint'

        # Agent-specific errors - retry failed step
        if any(keyword in error_lower for keyword in ['agent', 'review', 'draft']):
            return 'retry_failed_step'

        # Critical errors - try fallback
        if any(keyword in error_lower for keyword in ['critical', 'fatal', 'system']):
            return 'fallback_execution'

        # Default strategy
        return 'retry_from_checkpoint'

    async def _retry_from_checkpoint(self, workflow_id: str, workflow_data: Dict) -> RecoveryResult:
        """Retry workflow from last checkpoint."""
        try:
            # Find last successful checkpoint
            checkpoints = await self.checkpoint_manager.get_checkpoints(workflow_id)
            if not checkpoints:
                return RecoveryResult(
                    success=False,
                    message="No checkpoints available for recovery"
                )

            last_checkpoint = checkpoints[-1]

            # Restore workflow state to checkpoint
            await self.checkpoint_manager.restore_checkpoint(workflow_id, last_checkpoint['id'])

            # Resume workflow execution
            from workflows.email_workflow import EmailWorkflowOrchestrator
            orchestrator = EmailWorkflowOrchestrator()

            # Continue from checkpoint
            result = await orchestrator._resume_from_checkpoint(workflow_id, last_checkpoint)

            return RecoveryResult(
                success=True,
                message=f"Successfully recovered from checkpoint: {last_checkpoint['name']}",
                workflow_result=result,
                recovery_actions=['checkpoint_restore', 'workflow_resume']
            )

        except Exception as e:
            return RecoveryResult(
                success=False,
                message=f"Checkpoint recovery failed: {str(e)}"
            )
```

### Step 5: Testing Implementation
```python
# tests/test_email_workflow.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from workflows.email_workflow import EmailWorkflowOrchestrator, WorkflowStatus
from orchestration.agent_coordinator import AgentCoordinator

class TestEmailWorkflow:

    @pytest.fixture
    def orchestrator(self):
        """Create test orchestrator."""
        config = {
            'max_retry_attempts': 2,
            'timeout_seconds': 60,
            'enable_monitoring': False,
            'enable_recovery': False
        }
        return EmailWorkflowOrchestrator(config)

    @pytest.fixture
    def sample_task_data(self):
        """Sample task data for testing."""
        return {
            'recipient': 'test@example.com',
            'subject': 'Test Email',
            'content_requirements': {
                'tone': 'professional',
                'length': 'medium',
                'key_points': ['point1', 'point2']
            },
            'priority': 'medium'
        }

    @pytest.mark.asyncio
    async def test_complete_workflow_success(self, orchestrator, sample_task_data):
        """Test successful end-to-end workflow execution."""
        # Mock all agent interactions
        with patch.object(orchestrator.agent_coordinator, 'get_director_agent') as mock_director, \
             patch.object(orchestrator.agent_coordinator, 'get_communications_agent') as mock_comm, \
             patch.object(orchestrator.agent_coordinator, 'get_review_agents') as mock_review, \
             patch.object(orchestrator.agent_coordinator, 'get_email_agent') as mock_email:

            # Setup mocks
            mock_director.return_value.route_task = AsyncMock(return_value={'success': True, 'task_data': sample_task_data})
            mock_comm.return_value.create_draft = AsyncMock(return_value={'success': True, 'draft_content': 'Test draft'})
            mock_comm.return_value.finalize_draft = AsyncMock(return_value={'success': True, 'content': 'Final draft', 'subject': 'Test Subject'})

            mock_review_agent = Mock()
            mock_review_agent.review_draft = AsyncMock(return_value={'quality_score': 85, 'suggestions': []})
            mock_review.return_value = [(mock_review_agent, 'grammar')]

            mock_email.return_value.send_email = AsyncMock(return_value={'status': 'sent', 'email_id': 'email_123'})

            # Execute workflow
            result = await orchestrator.execute_email_workflow(sample_task_data)

            # Verify result
            assert result.status == WorkflowStatus.COMPLETED
            assert result.email_id == 'email_123'
            assert len(result.steps_completed) == 5
            assert result.execution_time is not None

    @pytest.mark.asyncio
    async def test_workflow_failure_and_recovery(self, orchestrator, sample_task_data):
        """Test workflow failure and recovery mechanism."""
        orchestrator.config['enable_recovery'] = True

        with patch.object(orchestrator.agent_coordinator, 'get_director_agent') as mock_director, \
             patch.object(orchestrator.recovery, 'attempt_recovery') as mock_recovery:

            # Setup failure
            mock_director.return_value.route_task = AsyncMock(side_effect=Exception("Network timeout"))

            # Setup recovery
            mock_recovery.return_value = Mock(
                success=True,
                workflow_result=Mock(
                    workflow_id='test_workflow',
                    status=WorkflowStatus.COMPLETED,
                    email_id='recovered_email_123'
                )
            )

            # Execute workflow
            result = await orchestrator.execute_email_workflow(sample_task_data)

            # Verify recovery was attempted
            mock_recovery.assert_called_once()
            assert result.email_id == 'recovered_email_123'

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, orchestrator, sample_task_data):
        """Test multiple concurrent workflow executions."""
        # Mock all dependencies
        with patch.object(orchestrator, '_execute_workflow_steps') as mock_execute:
            mock_execute.return_value = Mock(
                workflow_id='test',
                status=WorkflowStatus.COMPLETED,
                email_id='test_email',
                execution_time=1.5
            )

            # Execute multiple workflows concurrently
            tasks = [
                orchestrator.execute_email_workflow({**sample_task_data, 'recipient': f'test{i}@example.com'})
                for i in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 5
            for result in results:
                assert result.status == WorkflowStatus.COMPLETED
```

---

## 🧪 7. Testing & QA

### 7.1 Comprehensive Test Strategy
```bash
# Run all workflow tests
pytest tests/test_email_workflow.py -v --cov=workflows

# Run state management tests
pytest tests/test_state_management.py -v

# Run error recovery tests
pytest tests/test_error_recovery.py -v

# Run performance tests
pytest tests/test_performance.py -v --timeout=300

# Run integration tests
pytest tests/test_integration.py -v --integration
```

### 7.2 Load Testing
```python
# tests/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from workflows.email_workflow import EmailWorkflowOrchestrator

@pytest.mark.asyncio
async def test_workflow_performance_under_load():
    """Test workflow performance with multiple concurrent executions."""
    orchestrator = EmailWorkflowOrchestrator({
        'max_concurrent_workflows': 20,
        'timeout_seconds': 120
    })

    async def execute_workflow(workflow_id):
        task_data = {
            'recipient': f'test{workflow_id}@example.com',
            'subject': f'Test Email {workflow_id}',
            'content_requirements': {'tone': 'professional'}
        }

        start_time = time.time()
        result = await orchestrator.execute_email_workflow(task_data)
        duration = time.time() - start_time

        return {
            'workflow_id': result.workflow_id,
            'status': result.status,
            'duration': duration,
            'success': result.status == WorkflowStatus.COMPLETED
        }

    # Execute 20 concurrent workflows
    tasks = [execute_workflow(i) for i in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analyze results
    successful_workflows = [r for r in results if isinstance(r, dict) and r['success']]
    avg_duration = sum(r['duration'] for r in successful_workflows) / len(successful_workflows)

    # Performance assertions
    assert len(successful_workflows) >= 18  # 90% success rate
    assert avg_duration < 10.0  # Average under 10 seconds
    assert max(r['duration'] for r in successful_workflows) < 30.0  # Max under 30 seconds
```

### 7.3 Manual Testing Scenarios
```bash
# Test complete workflow
curl -X POST http://localhost:5000/api/v1/workflow/email \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "test@example.com",
    "subject": "Test Email",
    "content_requirements": {
      "tone": "professional",
      "length": "medium",
      "key_points": ["Introduction", "Main content", "Call to action"]
    }
  }'

# Monitor workflow progress
curl -X GET http://localhost:5000/api/v1/workflow/status/workflow_123

# Test error scenarios
curl -X POST http://localhost:5000/api/v1/workflow/email \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Test workflow cancellation
curl -X POST http://localhost:5000/api/v1/workflow/cancel/workflow_123
```

---

## 🔗 8. Integration & Related Tasks

### 8.1 Component Dependencies
This workflow orchestrator integrates the following components:
- **DirectorAgent** (task_003): Routes tasks to appropriate agents
- **CommunicationsDept** (task_005): Creates and finalizes email drafts
- **DraftReviewAgent** (task_006): Reviews and improves draft quality
- **EmailAgent** (task_007): Sends final emails via SMTP
- **Task API** (task_008): Receives initial task requests

### 8.2 Integration Architecture
```python
# Integration flow diagram
"""
API Request → DirectorAgent → CommunicationsDept → DraftReviewAgent → EmailAgent
     ↓              ↓               ↓                    ↓              ↓
State Tracking → Workflow Monitor → Error Recovery → Transaction Mgmt → Final Result
"""

# Integration validation
async def validate_agent_integration():
    """Validate all agent integrations work correctly."""
    coordinator = AgentCoordinator({})

    # Test each agent availability
    director = await coordinator.get_director_agent()
    assert hasattr(director, 'route_task')

    communications = await coordinator.get_communications_agent()
    assert hasattr(communications, 'create_draft')
    assert hasattr(communications, 'finalize_draft')

    review_agents = await coordinator.get_review_agents()
    assert len(review_agents) > 0

    email_agent = await coordinator.get_email_agent()
    assert hasattr(email_agent, 'send_email')
```

### 8.3 Data Flow Validation
```python
# Validate data consistency across workflow steps
def validate_data_flow(workflow_result):
    """Ensure data flows correctly through all workflow steps."""
    required_fields = [
        'workflow_id',
        'status',
        'email_id',
        'final_draft',
        'execution_time',
        'steps_completed'
    ]

    for field in required_fields:
        assert hasattr(workflow_result, field), f"Missing field: {field}"

    # Validate step completion order
    expected_steps = [
        'routing_completed',
        'draft_created',
        'review_completed',
        'draft_finalized',
        'email_sent'
    ]

    assert workflow_result.steps_completed == expected_steps
```

---

## ⚠️ 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Agent communication failures | Implement retry logic and circuit breakers |
| Workflow state corruption | Use Redis persistence and database backups |
| Memory leaks from long-running workflows | Implement resource cleanup and monitoring |
| Deadlocks in concurrent workflows | Use timeout mechanisms and lock ordering |
| Data inconsistency across agents | Implement transaction management and rollback |
| Performance degradation under load | Add rate limiting and resource pooling |

### 9.1 Error Handling Strategies
- **Graceful Degradation**: Continue workflow with reduced functionality
- **Circuit Breaker**: Prevent cascading failures across agents
- **Bulkhead Pattern**: Isolate failures to specific workflow components
- **Retry with Backoff**: Exponential backoff for transient failures
- **Dead Letter Queue**: Handle permanently failed workflows

### 9.2 Monitoring and Alerting
```python
# Critical alerts
ALERT_CONDITIONS = {
    'workflow_failure_rate': {'threshold': 0.1, 'window': '5m'},
    'avg_workflow_duration': {'threshold': 300, 'window': '10m'},
    'stuck_workflows': {'threshold': 5, 'window': '1m'},
    'agent_error_rate': {'threshold': 0.05, 'window': '5m'}
}

# Health checks
async def workflow_health_check():
    """Comprehensive workflow system health check."""
    health_status = {
        'redis_connection': await check_redis_connection(),
        'database_connection': await check_database_connection(),
        'agent_availability': await check_agent_availability(),
        'active_workflows': await get_active_workflow_count(),
        'error_rate': await calculate_error_rate()
    }

    overall_health = all(health_status.values())
    return {'healthy': overall_health, 'details': health_status}
```

---

## ✅ 10. Success Criteria

### 10.1 Functional Requirements
- [ ] Complete email workflow executes from API request to email delivery
- [ ] All workflow steps complete in correct sequence
- [ ] State tracking accurately reflects workflow progress
- [ ] Error recovery successfully handles common failure scenarios
- [ ] Transaction management maintains data consistency
- [ ] Concurrent workflows execute without interference
- [ ] Monitoring provides real-time workflow visibility

### 10.2 Performance Requirements
- [ ] Workflow completes within 5 minutes for standard emails
- [ ] System handles 50+ concurrent workflows
- [ ] Memory usage remains stable during extended operation
- [ ] Error recovery completes within 30 seconds
- [ ] State transitions occur within 1 second
- [ ] Database operations complete within timeout limits

### 10.3 Quality Requirements
- [ ] Unit test coverage >85% for all workflow components
- [ ] Integration tests validate end-to-end functionality
- [ ] Load testing confirms performance under expected load
- [ ] Error scenarios properly handled and logged
- [ ] Code follows established patterns and standards
- [ ] Documentation covers all public interfaces

### 10.4 Reliability Requirements
- [ ] Workflow success rate >95% under normal conditions
- [ ] Recovery success rate >80% for recoverable failures
- [ ] No data loss during workflow failures
- [ ] System remains responsive during high load
- [ ] Graceful degradation when components unavailable

---

## 🚀 11. Next Steps

### 11.1 Immediate Implementation
1. **Setup Infrastructure**: Configure Redis, database, and monitoring
2. **Implement Core Components**: Build workflow orchestrator and state management
3. **Agent Integration**: Connect all required agents with proper interfaces
4. **Testing Suite**: Develop comprehensive test coverage
5. **Performance Optimization**: Tune for expected load patterns

### 11.2 Production Deployment
1. **Security Review**: Audit workflow security and data handling
2. **Monitoring Setup**: Deploy metrics collection and alerting
3. **Load Testing**: Validate performance under production load
4. **Documentation**: Complete operational runbooks and troubleshooting guides
5. **Training**: Prepare team for workflow monitoring and maintenance

### 11.3 Future Enhancements
1. **Advanced Recovery**: Machine learning-based failure prediction
2. **Workflow Templates**: Pre-configured workflows for common scenarios
3. **Real-time Dashboard**: Live workflow monitoring interface
4. **Workflow Analytics**: Historical performance analysis and optimization
5. **Multi-tenant Support**: Isolated workflows for different users/organizations

### 11.4 Resources & Documentation
- **Workflow Patterns**: https://www.enterpriseintegrationpatterns.com/
- **Async Programming**: https://docs.python.org/3/library/asyncio.html
- **State Management**: Redis and database best practices
- **Monitoring**: Prometheus and Grafana setup guides
- **Error Recovery**: Circuit breaker and retry pattern implementations
