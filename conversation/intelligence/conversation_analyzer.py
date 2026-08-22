from conversation.intelligence.intent_analyzer import IntentAnalyzer
from conversation.intelligence.emotion_analyzer import EmotionAnalyzer
from conversation.intelligence.context_tracker import ContextTracker
from conversation.intelligence.response_strategy import ResponseStrategyEngine
from conversation.intelligence.conversation_state import ConversationState
from conversation.intelligence.language_analyzer import LanguageAnalyzer

class ConversationAnalyzer:
    """
    Master facade orchestrator for the Conversation Intelligence Layer.
    Executes intent, emotion, language, context, and strategy analysis to produce structured
    internal intelligence for Jarvis prompt assembly and conversation state updates.
    """

    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.context_tracker = ContextTracker()
        self.strategy_engine = ResponseStrategyEngine()
        self.language_analyzer = LanguageAnalyzer()
        self.state = ConversationState()

    def analyze_input(self, user_input: str) -> dict:
        """
        Runs comprehensive conversational analysis on the user input string.
        Returns the structured internal intelligence dictionary.
        """
        snapshot = self.state.get_snapshot()
        last_resp_type = snapshot.get("last_response_type")
        current_topic = snapshot.get("current_topic")

        # 1. Intent Analysis
        intent_data = self.intent_analyzer.analyze(user_input, last_response_type=last_resp_type)

        # 2. Emotion Analysis
        emotion_data = self.emotion_analyzer.analyze(user_input)

        # 3. Language & Style Analysis
        language_data = self.language_analyzer.analyze(user_input)

        # 4. Context & Topic Analysis
        context_data = self.context_tracker.analyze_topic_flow(user_input, current_topic=current_topic)

        # 5. Strategy Decision
        strategy_data = self.strategy_engine.decide_strategy(intent_data, emotion_data, context_data)

        # Combine into master structured analysis dict
        structured_analysis = {
            "intent": intent_data.get("intent"),
            "emotion": emotion_data.get("emotion"),
            "language": language_data.get("language"),
            "language_style": language_data.get("style"),
            "language_instruction": language_data.get("instruction"),
            "confidence": round(min(intent_data.get("confidence", 0.9), emotion_data.get("confidence", 0.9)), 2),
            "topic": context_data.get("topic"),
            "requires_follow_up": strategy_data.get("requires_follow_up"),
            "requires_clarification": strategy_data.get("requires_clarification"),
            "requires_suggestion": strategy_data.get("requires_suggestion"),
            "response_style": strategy_data.get("response_style"),
            "conversation_goal": strategy_data.get("conversation_goal"),
            "action_type": strategy_data.get("action_type"),
            "instruction": strategy_data.get("instruction")
        }


        # Update Conversation State
        action_type = strategy_data.get("action_type")
        pending_q = action_type if action_type in ["ask_follow_up", "ask_clarification"] else None

        self.state.update(
            current_topic=context_data.get("topic"),
            current_intent=intent_data.get("intent"),
            current_emotion=emotion_data.get("emotion"),
            last_user_message=user_input,
            conversation_goal=strategy_data.get("conversation_goal"),
            last_response_type=action_type,
            pending_question=pending_q
        )
        self.state.increment_turn()

        return structured_analysis

