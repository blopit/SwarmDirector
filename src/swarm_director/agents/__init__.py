"""
Agents package for SwarmDirector
Contains agent implementations and management functionality
"""

from .base_agent import BaseAgent
from .supervisor_agent import SupervisorAgent
from .worker_agent import WorkerAgent
from .director import DirectorAgent
from .draft_review_agent import DraftReviewAgent
from .email_agent import EmailAgent
from .communications_dept import CommunicationsDept

__all__ = [
    'BaseAgent',
    'SupervisorAgent',
    'WorkerAgent',
    'DirectorAgent',
    'DraftReviewAgent',
    'EmailAgent',
    'CommunicationsDept'
]