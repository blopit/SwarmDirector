#!/usr/bin/env python3
"""
SwarmDirector AutoGen Orchestration Demo
Demonstrates advanced multi-agent orchestration capabilities
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from swarm_director.utils.autogen_integration import (
        AutoGenConfig,
        OrchestrationPattern,
        ConversationConfig,
        ConversationDirector,
        AdvancedMultiAgentChain,
    )
    print("✅ Successfully imported orchestration modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure the src directory is properly set up")
    sys.exit(1)


def main():
    """Main demo function"""
    print("🚀 SWARM DIRECTOR AUTOGEN ORCHESTRATION DEMO")
    print("=" * 60)
    print(f"⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test orchestration patterns
        print("\n🎯 ORCHESTRATION PATTERNS:")
        for pattern in OrchestrationPattern:
            print(f"   • {pattern.value}")
        
        # Test conversation director
        print("\n🎬 CONVERSATION DIRECTOR:")
        director = ConversationDirector("DemoDirector")
        print(f"   Director: {director.name}")
        print(f"   Config: {director.config.model}")
        
        # Test advanced chain
        print("\n🔗 ADVANCED MULTI-AGENT CHAIN:")
        chain = AdvancedMultiAgentChain("DemoChain")
        print(f"   Chain: {chain.name}")
        print(f"   Pattern: {chain.conversation_config.pattern.value}")
        print(f"   Max rounds: {chain.conversation_config.max_round}")
        
        print("\n" + "="*60)
        print("✅ ORCHESTRATION DEMO COMPLETED SUCCESSFULLY")
        print("🚀 Ready for production multi-agent orchestration!")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
