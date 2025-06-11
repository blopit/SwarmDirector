"""
AutoGen integration helpers for SwarmDirector
"""

import autogen
from typing import Dict, List, Optional
from flask import current_app

def create_autogen_agent(agent_name: str, system_message: str, config: Dict) -> autogen.AssistantAgent:
    """Create an AutoGen agent with the specified configuration"""
    try:
        # Default configuration for AutoGen agents
        default_config = {
            "request_timeout": 600,
            "seed": 42,
            "config_list": config.get("llm_config", []),
            "temperature": 0.7,
        }
        
        # Merge with provided config
        llm_config = {**default_config, **config.get("llm_config", {})}
        
        # Create the agent
        agent = autogen.AssistantAgent(
            name=agent_name,
            system_message=system_message,
            llm_config=llm_config
        )
        
        current_app.logger.info(f"Created AutoGen agent: {agent_name}")
        return agent
        
    except Exception as e:
        current_app.logger.error(f"Error creating AutoGen agent {agent_name}: {str(e)}")
        raise

def create_user_proxy_agent(agent_name: str, config: Dict) -> autogen.UserProxyAgent:
    """Create an AutoGen UserProxy agent"""
    try:
        # Default configuration for UserProxy agents
        default_config = {
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 10,
            "is_termination_msg": lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            "code_execution_config": {
                "work_dir": "autogen_workspace",
                "use_docker": False,
            },
        }
        
        # Merge with provided config
        proxy_config = {**default_config, **config}
        
        # Create the user proxy agent
        agent = autogen.UserProxyAgent(
            name=agent_name,
            **proxy_config
        )
        
        current_app.logger.info(f"Created AutoGen UserProxy agent: {agent_name}")
        return agent
        
    except Exception as e:
        current_app.logger.error(f"Error creating AutoGen UserProxy agent {agent_name}: {str(e)}")
        raise

def setup_group_chat(agents: List[autogen.Agent], admin_name: str = "Admin") -> autogen.GroupChat:
    """Set up a group chat with multiple AutoGen agents"""
    try:
        # Create group chat
        groupchat = autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=50,
            admin_name=admin_name
        )
        
        # Create group chat manager
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": []}  # Configure as needed
        )
        
        current_app.logger.info(f"Created group chat with {len(agents)} agents")
        return groupchat, manager
        
    except Exception as e:
        current_app.logger.error(f"Error setting up group chat: {str(e)}")
        raise

def initiate_chat_with_agent(initiator_agent, recipient_agent, message: str, max_turns: int = 10) -> List[Dict]:
    """Initiate a chat between two AutoGen agents"""
    try:
        # Start the conversation
        chat_result = initiator_agent.initiate_chat(
            recipient_agent,
            message=message,
            max_turns=max_turns
        )
        
        current_app.logger.info(f"Chat completed between {initiator_agent.name} and {recipient_agent.name}")
        return chat_result.chat_history if hasattr(chat_result, 'chat_history') else []
        
    except Exception as e:
        current_app.logger.error(f"Error in agent chat: {str(e)}")
        raise

def get_default_llm_config(api_key: Optional[str] = None) -> Dict:
    """Get default LLM configuration for AutoGen agents"""
    return {
        "config_list": [
            {
                "model": "gpt-3.5-turbo",
                "api_key": api_key or current_app.config.get("OPENAI_API_KEY"),
            }
        ],
        "timeout": 120,
    }

def agent_to_database_mapping(autogen_agent, db_agent):
    """Map AutoGen agent properties to database agent model"""
    try:
        # Update database agent with AutoGen agent information
        autogen_config = {
            "name": autogen_agent.name,
            "system_message": getattr(autogen_agent, 'system_message', ''),
            "llm_config": getattr(autogen_agent, 'llm_config', {}),
        }
        
        db_agent.autogen_config = autogen_config
        db_agent.system_message = getattr(autogen_agent, 'system_message', '')
        db_agent.save()
        
        current_app.logger.info(f"Mapped AutoGen agent {autogen_agent.name} to database")
        
    except Exception as e:
        current_app.logger.error(f"Error mapping agent to database: {str(e)}")
        raise

def create_specialized_agents() -> Dict[str, autogen.Agent]:
    """Create a set of specialized agents for common tasks"""
    agents = {}
    
    try:
        # Code review agent
        agents['code_reviewer'] = create_autogen_agent(
            agent_name="CodeReviewer",
            system_message="You are a senior software engineer specializing in code review. "
                          "Analyze code for bugs, performance issues, and best practices.",
            config={"llm_config": get_default_llm_config()}
        )
        
        # Task planner agent
        agents['task_planner'] = create_autogen_agent(
            agent_name="TaskPlanner",
            system_message="You are a project manager who excels at breaking down complex "
                          "tasks into manageable subtasks and creating execution plans.",
            config={"llm_config": get_default_llm_config()}
        )
        
        # Quality assurance agent
        agents['qa_tester'] = create_autogen_agent(
            agent_name="QATester",
            system_message="You are a quality assurance specialist focused on testing "
                          "strategies, test case creation, and bug identification.",
            config={"llm_config": get_default_llm_config()}
        )
        
        current_app.logger.info(f"Created {len(agents)} specialized agents")
        return agents
        
    except Exception as e:
        current_app.logger.error(f"Error creating specialized agents: {str(e)}")
        raise 