class ResponseStrategyEngine:
    """
    Evaluates intent, emotion, and context analysis to select the optimal
    Response Strategy for Jarvis (answering directly, asking follow-ups, requesting clarification,
    providing suggestions, acknowledging emotion, or celebrating success).
    """

    def decide_strategy(self, intent_data: dict, emotion_data: dict, context_data: dict) -> dict:
        intent = intent_data.get("intent", "statement_task")
        emotion = emotion_data.get("emotion", "neutral")
        topic = context_data.get("topic", "general conversation")
        
        req_clarification = intent_data.get("requires_clarification", False)
        req_followup = intent_data.get("requires_follow_up", False)
        req_suggestion = intent_data.get("requires_suggestion", False)

        # 1. Ambiguous Request -> Clarification Strategy
        if req_clarification or intent == "ambiguous_request":
            return {
                "action_type": "ask_clarification",
                "response_style": "clarifying",
                "requires_follow_up": True,
                "requires_clarification": True,
                "requires_suggestion": False,
                "conversation_goal": "clarify what the user wants to inspect or fix before acting",
                "instruction": "Ask the user specifically what 'this' or the request refers to instead of guessing."
            }

        # 2. Excited / Success -> Celebration Strategy
        if emotion == "excited" or (emotion == "happy" and intent == "emotional_expression"):
            return {
                "action_type": "celebrate_success",
                "response_style": "celebratory",
                "requires_follow_up": False,
                "requires_clarification": False,
                "requires_suggestion": False,
                "conversation_goal": "celebrate the user's success naturally and enthusiastically",
                "instruction": "Respond naturally and positively to the user's victory without giving generic technical explanations."
            }

        # 3. Frustrated / Sad / Angry -> Empathetic Support Strategy
        if emotion in ["frustrated", "sad", "angry"]:
            return {
                "action_type": "acknowledge_emotion",
                "response_style": "empathic_helpful",
                "requires_follow_up": True,
                "requires_clarification": False,
                "requires_suggestion": True,
                "conversation_goal": "acknowledge user frustration empathetically and offer practical assistance",
                "instruction": "First acknowledge the user's emotion empathetically and supportively (e.g., 'Arre Boss, tension mat lo 😄'), then offer simple, calm assistance to solve the problem step-by-step."
            }

        # 4. Vague High-Level Goal (e.g. "I want to build an app") -> Curious Probing Strategy
        if intent == "vague_building_request":
            return {
                "action_type": "ask_follow_up",
                "response_style": "curious_probing",
                "requires_follow_up": True,
                "requires_clarification": False,
                "requires_suggestion": True,
                "conversation_goal": "understand user vision and problem statement before providing tutorials or steps",
                "instruction": "Do NOT dump a tutorial, numbered list, or multiple questions. Ask exactly ONE targeted, natural follow-up question (e.g., 'Nice Boss. App kis problem ko solve karega?')."
            }

        # 5. Opinion Request -> Reasoning Strategy
        if intent == "opinion_request":
            return {
                "action_type": "provide_suggestions",
                "response_style": "explanatory",
                "requires_follow_up": False,
                "requires_clarification": False,
                "requires_suggestion": True,
                "conversation_goal": "provide thoughtful analysis and clear opinion with sound reasoning",
                "instruction": "Do NOT blindly agree. Analyze the situation thoughtfully and respectfully share your honest opinion with clear reasoning (e.g. explain why isolating responsibilities prevents future maintenance debt)."
            }

        # 6. Suggestion Request -> Helpful Suggestions Strategy
        if intent == "suggestion_request" or req_suggestion:
            return {
                "action_type": "provide_suggestions",
                "response_style": "concise",
                "requires_follow_up": True,
                "requires_clarification": False,
                "requires_suggestion": True,
                "conversation_goal": "provide concise, practical suggestions or alternatives",
                "instruction": "Offer 2-3 concise, practical suggestions or recommendations tailored to the topic."
            }

        # 7. Casual Chat -> Conversational Strategy
        if intent == "casual_chat":
            return {
                "action_type": "answer_directly",
                "response_style": "concise",
                "requires_follow_up": False,
                "requires_clarification": False,
                "requires_suggestion": False,
                "conversation_goal": "maintain a friendly, concise, natural conversation",
                "instruction": "Respond naturally and concisely without repetitive phrases like 'How can I assist you today?'."
            }

        # 8. Standard Factual Question -> Direct Answer Strategy
        return {
            "action_type": "answer_directly",
            "response_style": "concise",
            "requires_follow_up": False,
            "requires_clarification": False,
            "requires_suggestion": False,
            "conversation_goal": "answer the question directly and concisely",
            "instruction": "Be concise and direct. Answer the question directly using stored memory or general knowledge."
        }
