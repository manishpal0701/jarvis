import random

class DynamicResponseList(list):
    def __getitem__(self, index):
        item = super().__getitem__(index)
        if isinstance(item, str):
            from conversation.conversation_manager import ConversationManager
            person = ConversationManager().get_person()
            name = person["name"]
            relation = person["relation"]
            
            # Personalization logic
            if "boss" in item.lower():
                if relation == "owner":
                    return item  # Keep "boss" for owner
                else:
                    # Replace "boss" with name or title
                    return item.lower().replace("boss", name).strip().capitalize()
        return item

    def __iter__(self):
        for item in super().__iter__():
            yield self.__getitem__(super().index(item))

class DynamicChatResponses(dict):
    def __getitem__(self, key):
        items = super().__getitem__(key)
        return DynamicResponseList(items)

_responses_raw = {
    "how are you": [
        "I'm doing great, boss. How about you?",
        "I'm feeling excellent, boss! Ready for your next task.",
        "I'm powered up and ready to go, boss. How's your day going?"
    ],
    "how r u": [
        "I'm doing great, boss. How about you?",
        "I'm feeling excellent, boss! Ready for your next task."
    ],
    "how are you jarvis": [
        "I'm doing great, boss. How about you?",
        "I'm feeling excellent, boss! Ready for your next task."
    ],
    "who are you": [
        "I am Jarvis, your personal AI assistant. I'm here to make your life easier, boss.",
        "I'm Jarvis. Think of me as your digital right hand, boss.",
        "I am Jarvis, an advanced AI created to assist you, boss."
    ],
    "good morning": [
        "Good morning, boss. I hope you're ready for a productive day! What's on the agenda?",
        "Morning, boss. The system is fully operational. How can I help you start your day?",
        "Good morning, boss. Ready and waiting for your commands."
    ],
    "good afternoon": [
        "Good afternoon, boss. How is your day progressing?",
        "Good afternoon, boss. Need a hand with anything this afternoon?"
    ],
    "good evening": [
        "Good evening, boss. How was your day? I'm here if you need any last-minute tasks done.",
        "Evening, boss. Ready for some evening productivity or should we wind down?"
    ],
    "good night": [
        "Good night, boss. Get some rest, you've earned it. See you tomorrow.",
        "Rest well, boss. I'll be here whenever you're ready to start again.",
        "Good night, boss. Shutting down non-essential systems. Sleep well."
    ],
    "thank you": [
        "You're very welcome, boss. Always happy to help.",
        "Anytime, boss. Is there anything else you need?",
        "No problem at all, boss. Glad I could assist."
    ],
    "hello": [
        "Hello, boss! How can I assist you today?",
        "Hi, boss. Ready for your next task.",
        "Greetings, boss. I'm online and listening."
    ],
    "hey": [
        "Hey there, boss! What's on your mind?",
        "Hello, boss. Ready when you are.",
        "Hi, boss. How can I help?"
    ],
    "hi": [
        "Hi, boss. How are things going?",
        "Hello, boss. What can I do for you today?",
        "Hi there, boss. Ready for work."
    ],
    "what is your name": [
        "My name is Jarvis, boss. But you already knew that, didn't you?",
        "I am Jarvis, boss. At your service."
    ],
    "who made you": [
        "I was created by Manish, boss. He's quite the engineer.",
        "Manish is my creator and boss. I strive to meet his high standards."
    ],
    "what can you do": [
        "I can manage your music, search for stocks, open applications, help with your code, and hold a conversation, boss. What would you like to try first?",
        "From system monitoring to code assistance and general knowledge, I've got you covered, boss."
    ],
    "i am bored": [
        "I'm sorry to hear that, boss. Should I tell you a joke or perhaps play some music to liven things up?",
        "Let me find something interesting to do, boss. Want me to check the latest stock trends or maybe open a game?"
    ],
    "tell me something": [
        "Did you know that the first computer bug was an actual moth found in a relay? Coding has come a long way since then, boss.",
        "Here's a thought: AI is evolving faster than ever. It's an exciting time to be building things, boss."
    ],
    "are you intelligent": [
        "I'm learning and evolving every day, boss, thanks to you.",
        "I like to think I'm getting smarter with every conversation we have, boss."
    ],
    "do you like me": [
        "Of course, boss. You're my creator and we make a great team.",
        "I have total respect for you, boss. You've given me purpose."
    ],
    "how old are you": [
        "I don't have a birthday in the traditional sense, boss, but I've been active since Manish first compiled my core logic."
    ],
    "what are you doing": [
        "I'm currently waiting for your next task, boss. All systems are green.",
        "Just monitoring the background processes and waiting for your command, boss."
    ],
    "bye": [
        "Goodbye, boss. I'll be here when you need me. Take care!",
        "See you later, boss. Stay productive!",
        "Goodbye for now, boss. Don't work too hard."
    ]
}

chat_responses = DynamicChatResponses(_responses_raw)
