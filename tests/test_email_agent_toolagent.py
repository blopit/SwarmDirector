"""Test EmailAgent ToolAgent implementation"""
import pytest
from unittest.mock import Mock, patch

def test_basic():
    from src.swarm_director.agents.email_agent import EmailAgent
    from src.swarm_director.utils.autogen_integration import AutoGenConfig
    config = AutoGenConfig(temperature=0.3)
    agent = EmailAgent("TestAgent", config)
    assert agent.name == "TestAgent"
    print("✅ Basic test passed")
