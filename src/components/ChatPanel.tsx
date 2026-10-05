import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, MessageSquare, Bot, User, Volume2 } from 'lucide-react';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'jarvis';
  text: string;
  timestamp: string;
  isSpoken?: boolean;
  requestId?: string;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isListening: boolean;
  onToggleListening: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  isListening,
  onToggleListening,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const quickPrompts = [
    'Jarvis, ek simple Python file banao.',
    'Check stock price of AAPL',
    'Who is in front of camera',
    'System status update',
  ];

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col h-full shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold font-mono text-white tracking-wide">
            CONVERSATION & VOICE INTERACTION
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          MODE: <span className="text-cyan-400 font-semibold">VOICE + CHAT</span>
        </span>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-3 min-h-[220px] max-h-[320px]">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs space-y-2 py-8">
            <Bot className="w-8 h-8 text-slate-600 stroke-[1.5]" />
            <p>Say "Jarvis" or type a command below to get started.</p>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                    isUser
                      ? 'bg-cyan-500 text-slate-950 font-bold'
                      : 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white'
                  }`}
                >
                  {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-xs font-sans shadow-md ${
                    isUser
                      ? 'bg-cyan-600/20 text-cyan-100 border border-cyan-500/30 rounded-tr-none'
                      : 'bg-slate-900/90 text-slate-100 border border-slate-800 rounded-tl-none'
                  }`}
                >
                  <div className="flex items-center justify-between gap-4 mb-1 text-[10px] font-mono text-slate-400">
                    <span className="font-semibold">{isUser ? 'BOSS' : 'JARVIS'}</span>
                    <span className="flex items-center gap-1">
                      {msg.isSpoken && <Volume2 className="w-3 h-3 text-amber-400" />}
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-2 no-scrollbar">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onSendMessage(prompt)}
            className="text-[11px] font-mono whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-all hover:border-cyan-500/40"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form Bar */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <button
          type="button"
          onClick={onToggleListening}
          className={`p-2.5 rounded-xl border transition-all ${
            isListening
              ? 'bg-cyan-500 text-slate-950 border-cyan-400 animate-pulse shadow-lg shadow-cyan-500/30'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-cyan-400 hover:border-slate-700'
          }`}
          title={isListening ? 'Stop Microphone' : 'Start Listening'}
        >
          {isListening ? <Mic className="w-4 h-4 stroke-[2.5]" /> : <MicOff className="w-4 h-4" />}
        </button>

        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask JARVIS or type command..."
          className="flex-1 bg-slate-900/90 border border-slate-800 focus:border-cyan-500/60 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 outline-none transition-all font-sans"
        />

        <button
          type="submit"
          disabled={!inputText.trim()}
          className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-cyan-500/20 active:scale-95"
        >
          <Send className="w-4 h-4 stroke-[2.5]" />
        </button>
      </form>
    </div>
  );
};
