"""
Models package for SwarmDirector
Contains database models for the hierarchical AI agent system
"""

from .base import db
from .agent import Agent
from .task import Task
from .conversation import Conversation, Message, ConversationAnalytics
from .agent_log import AgentLog
from .draft import Draft
from .email_message import EmailMessage
from .cost_tracking import APIUsage, CostBudget, CostAlert
from .validation import ValidationRecord, QualityGateConfig, RollbackRecord
from .plugin import PluginRecord, PluginInstallation, CapabilityGap, AgentTemplate
from .analytics import TaskMetrics, TaskAnalyticsInsight, TaskPerformanceSnapshot

__all__ = [
    'db', 
    'Agent', 
    'Task', 
    'Conversation', 
    'Message', 
    'ConversationAnalytics',
    'AgentLog', 
    'Draft', 
    'EmailMessage', 
    'APIUsage', 
    'CostBudget', 
    'CostAlert',
    'ValidationRecord',
    'QualityGateConfig', 
    'RollbackRecord',
    'PluginRecord',
    'PluginInstallation',
    'CapabilityGap',
    'AgentTemplate',
    'TaskMetrics',
    'TaskAnalyticsInsight',
    'TaskPerformanceSnapshot'
]