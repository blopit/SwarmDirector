"""
AutoGen Configuration Management for SwarmDirector
Handles environment variables, API keys, and agent configurations
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from flask import current_app


@dataclass
class AutoGenEnvironmentConfig:
    """Environment configuration for AutoGen"""
    openai_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    workspace_dir: str = "autogen_workspace"
    use_docker: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> "AutoGenEnvironmentConfig":
        """Create configuration from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY") or current_app.config.get("OPENAI_API_KEY"),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            workspace_dir=os.getenv("AUTOGEN_WORKSPACE", "autogen_workspace"),
            use_docker=os.getenv("AUTOGEN_USE_DOCKER", "false").lower() == "true",
            log_level=os.getenv("AUTOGEN_LOG_LEVEL", "INFO")
        )

    def get_config_list(self, model_preference: str = "openai") -> List[Dict]:
        """Get config list for AutoGen based on available API keys"""
        config_list = []

        if model_preference == "openai" and self.openai_api_key:
            config_list.extend([
                {"model": "gpt-4", "api_key": self.openai_api_key},
                {"model": "gpt-3.5-turbo", "api_key": self.openai_api_key},
            ])

        if model_preference == "azure" and self.azure_openai_api_key and self.azure_openai_endpoint:
            config_list.extend([
                {
                    "model": "gpt-4",
                    "api_key": self.azure_openai_api_key,
                    "base_url": self.azure_openai_endpoint,
                    "api_type": "azure",
                    "api_version": "2023-05-15"
                }
            ])

        if model_preference == "anthropic" and self.anthropic_api_key:
            config_list.extend([
                {"model": "claude-3-opus-20240229", "api_key": self.anthropic_api_key},
                {"model": "claude-3-sonnet-20240229", "api_key": self.anthropic_api_key},
            ])

        if model_preference == "google" and self.google_api_key:
            config_list.extend([
                {"model": "gemini-pro", "api_key": self.google_api_key},
            ])

        # Fallback to any available API key
        if not config_list:
            if self.openai_api_key:
                config_list.append({"model": "gpt-3.5-turbo", "api_key": self.openai_api_key})

        return config_list


def setup_autogen_environment() -> AutoGenEnvironmentConfig:
    """Setup and validate AutoGen environment"""
    config = AutoGenEnvironmentConfig.from_environment()

    # Create workspace directory if it doesn't exist
    os.makedirs(config.workspace_dir, exist_ok=True)

    # Validate at least one API key is available
    has_api_key = any([
        config.openai_api_key,
        config.azure_openai_api_key,
        config.anthropic_api_key,
        config.google_api_key
    ])

    if not has_api_key:
        raise ValueError(
            "No API keys found. Please set at least one of: "
            "OPENAI_API_KEY, AZURE_OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY"
        )

    return config


# Predefined agent configurations
AGENT_TEMPLATES = {
    "code_reviewer": {
        "name": "CodeReviewer",
        "role": "code_reviewer",
        "type": "chat",
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "system_message": (
            "You are a senior software engineer specializing in code review. "
            "Analyze code for bugs, security issues, performance problems, "
            "and adherence to best practices. Provide constructive feedback "
            "with specific suggestions for improvement."
        )
    },
    
    "task_planner": {
        "name": "TaskPlanner",
        "role": "task_planner", 
        "type": "chat",
        "model": "gpt-3.5-turbo",
        "temperature": 0.5,
        "max_tokens": 1500,
        "system_message": (
            "You are an expert project manager who excels at breaking down "
            "complex tasks into manageable subtasks. Create detailed execution "
            "plans with clear dependencies, timelines, and resource requirements."
        )
    },

    "qa_tester": {
        "name": "QATester",
        "role": "qa_tester",
        "type": "chat", 
        "model": "gpt-3.5-turbo",
        "temperature": 0.4,
        "max_tokens": 1500,
        "system_message": (
            "You are a quality assurance specialist focused on comprehensive "
            "testing strategies. Create test cases, identify edge cases, "
            "and suggest testing approaches for maximum code coverage."
        )
    },

    "architect": {
        "name": "Architect",
        "role": "architect",
        "type": "chat",
        "model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 2000,
        "system_message": (
            "You are a senior software architect responsible for system design "
            "and technical decision making. Focus on scalability, maintainability, "
            "security, and performance in your architectural recommendations."
        )
    },

    "tool_executor": {
        "name": "ToolExecutor",
        "role": "tool_executor",
        "type": "tool",
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1000,
        "system_message": (
            "You are a tool execution agent capable of running code and "
            "using various tools to complete tasks. Focus on safe, efficient "
            "execution and provide clear output summaries."
        )
    }
}


def get_agent_template(template_name: str) -> Dict:
    """Get predefined agent template configuration"""
    if template_name not in AGENT_TEMPLATES:
        raise ValueError(f"Unknown agent template: {template_name}")
    return AGENT_TEMPLATES[template_name].copy()


def create_development_team_config() -> List[Dict]:
    """Create a configuration for a complete development team"""
    return [
        get_agent_template("architect"),
        get_agent_template("task_planner"), 
        get_agent_template("code_reviewer"),
        get_agent_template("qa_tester"),
        get_agent_template("tool_executor")
    ] 