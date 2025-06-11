"""
Conversation Analytics Engine for AutoGen Conversations
Provides comprehensive analysis, metrics calculation, and insights for multi-agent conversations
"""

import json
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re
from ..models.conversation import Conversation, Message, ConversationAnalytics, MessageType, OrchestrationPattern
from ..models.base import db


class ConversationAnalyticsEngine:
    """Core analytics engine for conversation analysis and metrics calculation"""
    
    def __init__(self):
        self.sentiment_keywords = {
            'positive': ['good', 'great', 'excellent', 'perfect', 'amazing', 'wonderful', 'success', 'solved', 'completed'],
            'negative': ['bad', 'terrible', 'awful', 'problem', 'error', 'failed', 'issue', 'wrong', 'broken'],
            'neutral': ['okay', 'fine', 'normal', 'standard', 'regular', 'typical']
        }
    
    def analyze_conversation(self, conversation_id: int) -> Optional[ConversationAnalytics]:
        """Perform comprehensive analysis of a conversation"""
        conversation = Conversation.query.get(conversation_id)
        if not conversation or not conversation.messages:
            return None
        
        # Check if analytics already exist
        analytics = ConversationAnalytics.query.filter_by(conversation_id=conversation_id).first()
        if not analytics:
            analytics = ConversationAnalytics(conversation_id=conversation_id)
        
        # Calculate all metrics
        self._calculate_timing_metrics(conversation, analytics)
        self._calculate_content_metrics(conversation, analytics)
        self._calculate_participation_metrics(conversation, analytics)
        self._calculate_quality_metrics(conversation, analytics)
        self._calculate_autogen_metrics(conversation, analytics)
        self._calculate_sentiment_metrics(conversation, analytics)
        
        # Save analytics
        analytics.save()
        return analytics
    
    def _calculate_timing_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate timing-related metrics"""
        messages = sorted(conversation.messages, key=lambda m: m.created_at)
        
        if len(messages) < 2:
            return
        
        # Total duration
        start_time = messages[0].created_at
        end_time = messages[-1].created_at
        total_duration = (end_time - start_time).total_seconds()
        analytics.total_duration = total_duration
        
        # Message intervals
        intervals = []
        for i in range(1, len(messages)):
            interval = (messages[i].created_at - messages[i-1].created_at).total_seconds()
            intervals.append(interval)
        
        if intervals:
            analytics.avg_message_interval = statistics.mean(intervals)
        
        # Response times from message metadata
        response_times = [msg.response_time for msg in messages if msg.response_time]
        if response_times:
            analytics.fastest_response = min(response_times)
            analytics.slowest_response = max(response_times)
    
    def _calculate_content_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate content-related metrics"""
        all_content = []
        total_chars = 0
        message_lengths = []
        
        for message in conversation.messages:
            content = message.content or ""
            all_content.append(content.lower())
            char_count = len(content)
            total_chars += char_count
            message_lengths.append(char_count)
            
            # Update message length in the message record
            message.message_length = char_count
        
        analytics.total_characters = total_chars
        if message_lengths:
            analytics.avg_message_length = statistics.mean(message_lengths)
        
        # Vocabulary analysis
        all_text = " ".join(all_content)
        words = re.findall(r'\b\w+\b', all_text)
        unique_words = set(words)
        
        analytics.unique_words = len(unique_words)
        if words:
            analytics.vocabulary_richness = len(unique_words) / len(words)
    
    def _calculate_participation_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate participation-related metrics"""
        # Count messages per agent
        agent_message_counts = Counter()
        agent_names = set()
        
        for message in conversation.messages:
            if message.sender_agent_id:
                agent_message_counts[message.sender_agent_id] += 1
            if message.agent_name:
                agent_names.add(message.agent_name)
        
        analytics.total_participants = len(agent_message_counts) or len(agent_names)
        
        if agent_message_counts:
            # Most active agent
            most_active_id = agent_message_counts.most_common(1)[0][0]
            most_active_agent = next((msg.agent_name for msg in conversation.messages 
                                    if msg.sender_agent_id == most_active_id), str(most_active_id))
            analytics.most_active_agent = most_active_agent
            
            # Participation balance (0-1 score, 1 being perfectly balanced)
            message_counts = list(agent_message_counts.values())
            if len(message_counts) > 1:
                mean_count = statistics.mean(message_counts)
                variance = statistics.variance(message_counts)
                # Normalize variance to 0-1 scale (lower variance = better balance)
                analytics.participation_balance = max(0, 1 - (variance / mean_count if mean_count > 0 else 1))
            else:
                analytics.participation_balance = 1.0  # Single participant is perfectly balanced
    
    def _calculate_quality_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate quality-related metrics"""
        # Count error messages
        error_count = sum(1 for msg in conversation.messages if msg.message_type == MessageType.ERROR_MESSAGE)
        analytics.error_count = error_count
        
        # Completion status
        analytics.completion_status = conversation.status.value
        
        # Goal achievement (simple heuristic based on conversation completion and error rate)
        if conversation.status.value == 'completed':
            base_score = 80
            error_penalty = min(20, error_count * 5)  # 5 points per error, max 20 penalty
            analytics.goal_achievement = max(0, base_score - error_penalty)
        elif conversation.status.value == 'active':
            analytics.goal_achievement = 50  # Ongoing
        else:
            analytics.goal_achievement = 20  # Paused or error state
    
    def _calculate_autogen_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate AutoGen-specific metrics"""
        # Orchestration switches (if tracked in conversation history)
        autogen_history = conversation.autogen_chat_history or []
        
        # Simple orchestration efficiency based on message flow
        if isinstance(autogen_history, list) and len(autogen_history) > 1:
            speaker_changes = 0
            last_speaker = None
            
            for entry in autogen_history:
                if isinstance(entry, dict):
                    current_speaker = entry.get('name', entry.get('speaker'))
                    if last_speaker and current_speaker != last_speaker:
                        speaker_changes += 1
                    last_speaker = current_speaker
            
            # Group chat efficiency (more speaker changes can indicate good collaboration)
            if len(autogen_history) > 0:
                analytics.group_chat_efficiency = min(100, (speaker_changes / len(autogen_history)) * 100)
        
        # Agent collaboration score (based on response patterns and participation)
        agent_responses = defaultdict(int)
        agent_interactions = defaultdict(set)
        
        for i, message in enumerate(conversation.messages):
            if message.sender_agent_id:
                agent_responses[message.sender_agent_id] += 1
                
                # Check for agent-to-agent interactions
                if i > 0 and conversation.messages[i-1].sender_agent_id:
                    prev_agent = conversation.messages[i-1].sender_agent_id
                    if prev_agent != message.sender_agent_id:
                        agent_interactions[message.sender_agent_id].add(prev_agent)
        
        # Collaboration score based on variety of interactions
        if agent_responses:
            total_agents = len(agent_responses)
            avg_interactions = sum(len(interactions) for interactions in agent_interactions.values()) / total_agents
            analytics.agent_collaboration_score = min(100, avg_interactions * 20)  # Scale to 0-100
    
    def _calculate_sentiment_metrics(self, conversation: Conversation, analytics: ConversationAnalytics):
        """Calculate sentiment-related metrics"""
        sentiment_scores = []
        
        for message in conversation.messages:
            content = (message.content or "").lower()
            sentiment_score = self._analyze_message_sentiment(content)
            sentiment_scores.append(sentiment_score)
            
            # Update message sentiment
            message.sentiment_score = sentiment_score
        
        if sentiment_scores:
            analytics.overall_sentiment = statistics.mean(sentiment_scores)
            analytics.sentiment_variance = statistics.variance(sentiment_scores) if len(sentiment_scores) > 1 else 0
    
    def _analyze_message_sentiment(self, content: str) -> float:
        """Simple sentiment analysis based on keyword matching"""
        words = re.findall(r'\b\w+\b', content.lower())
        
        positive_count = sum(1 for word in words if word in self.sentiment_keywords['positive'])
        negative_count = sum(1 for word in words if word in self.sentiment_keywords['negative'])
        
        if positive_count + negative_count == 0:
            return 0.0  # Neutral
        
        # Calculate sentiment score (-1 to 1)
        sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        return max(-1, min(1, sentiment))
    
    def get_conversation_insights(self, conversation_id: int) -> Dict[str, Any]:
        """Get comprehensive insights for a conversation"""
        conversation = Conversation.query.get(conversation_id)
        analytics = ConversationAnalytics.query.filter_by(conversation_id=conversation_id).first()
        
        if not conversation:
            return {"error": "Conversation not found"}
        
        if not analytics:
            analytics = self.analyze_conversation(conversation_id)
        
        insights = {
            "conversation": conversation.to_dict(),
            "analytics": analytics.to_dict() if analytics else None,
            "summary": self._generate_summary(conversation, analytics),
            "recommendations": self._generate_recommendations(conversation, analytics)
        }
        
        return insights
    
    def _generate_summary(self, conversation: Conversation, analytics: Optional[ConversationAnalytics]) -> Dict[str, str]:
        """Generate a human-readable summary of the conversation"""
        if not analytics:
            return {"error": "Analytics not available"}
        
        summary = {}
        
        # Duration summary
        if analytics.total_duration:
            duration_mins = analytics.total_duration / 60
            summary["duration"] = f"Conversation lasted {duration_mins:.1f} minutes"
        
        # Participation summary
        summary["participation"] = f"{analytics.total_participants or 0} agents participated"
        if analytics.most_active_agent:
            summary["most_active"] = f"Most active agent: {analytics.most_active_agent}"
        
        # Quality summary
        efficiency_score = analytics.calculate_efficiency_score()
        quality_score = analytics.calculate_quality_score()
        summary["performance"] = f"Efficiency: {efficiency_score:.1f}%, Quality: {quality_score:.1f}%"
        
        # Sentiment summary
        if analytics.overall_sentiment is not None:
            sentiment_desc = "positive" if analytics.overall_sentiment > 0.1 else "negative" if analytics.overall_sentiment < -0.1 else "neutral"
            summary["sentiment"] = f"Overall sentiment: {sentiment_desc} ({analytics.overall_sentiment:.2f})"
        
        return summary
    
    def _generate_recommendations(self, conversation: Conversation, analytics: Optional[ConversationAnalytics]) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        if not analytics:
            return ["Unable to generate recommendations without analytics"]
        
        recommendations = []
        
        # Efficiency recommendations
        if analytics.avg_message_interval and analytics.avg_message_interval > 300:  # > 5 minutes
            recommendations.append("Consider optimizing agent response times to improve conversation flow")
        
        # Participation recommendations
        if analytics.participation_balance and analytics.participation_balance < 0.5:
            recommendations.append("Conversation participation is imbalanced - consider adjusting orchestration patterns")
        
        # Quality recommendations
        if analytics.error_count and analytics.error_count > 0:
            recommendations.append("Consider improving error handling to reduce conversation disruptions")
        
        # Sentiment recommendations
        if analytics.overall_sentiment and analytics.overall_sentiment < -0.2:
            recommendations.append("Overall sentiment is negative - review conversation goals and agent interactions")
        
        # AutoGen specific recommendations
        if analytics.group_chat_efficiency and analytics.group_chat_efficiency < 30:
            recommendations.append("Group chat efficiency is low - consider adjusting speaker selection patterns")
        
        if not recommendations:
            recommendations.append("Conversation performance looks good! No specific recommendations at this time.")
        
        return recommendations


# Factory function for easy access
def create_analytics_engine() -> ConversationAnalyticsEngine:
    """Create and return a conversation analytics engine instance"""
    return ConversationAnalyticsEngine()
