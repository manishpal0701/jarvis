import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { AvatarCore } from './components/AvatarCore';
import { ExecutionPanel, ProgressEventItem } from './components/ExecutionPanel';
import { ChatPanel, ChatMessage } from './components/ChatPanel';
import { CapabilitiesGrid } from './components/CapabilitiesGrid';
import { AudioEngine } from './components/AudioEngine';

export const App: React.FC = () => {
  const [jarvisState, setJarvisState] = useState<string>('IDLE');
  const [backendHealth, setBackendHealth] = useState<boolean>(false);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<string>('IDLE');
  const [progressEvents, setProgressEvents] = useState<ProgressEventItem[]>([]);
  const [hasError, setHasError] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'jarvis',
      text: 'JARVIS online. All systems operational. How may I assist you today, Boss?',
      timestamp: new Date().isoformat(),
    },
  ]);

  const wsRef = useRef<WebSocket | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const enqueuedAudioUrlsRef = useRef<Set<string>>(new Set());

  // Unified Assistant Message Aggregator (One assistant message per request_id)
  const upsertJarvisMessage = useCallback((data: {
    request_id?: string;
    speech_id?: string;
    text?: string;
    full_text?: string;
    isChunk?: boolean;
    isSpoken?: boolean;
    isFinal?: boolean;
    timestamp?: string;
  }) => {
    const reqKey = data.request_id || activeRequestId || null;
    const incomingText = data.full_text || data.text || '';
    if (!incomingText) return;

    setChatMessages((prev) => {
      // STRICT: Find existing assistant message by request_id ONLY.
      // Only fall back to last-jarvis heuristic if no request_id is available at all.
      let existingIdx = -1;
      if (reqKey) {
        existingIdx = prev.findIndex(
          (m) => m.sender === 'jarvis' && (m.requestId === reqKey || m.id === reqKey)
        );
      }
      // Heuristic fallback: only if no reqKey available (should be rare)
      if (existingIdx === -1 && !reqKey && prev.length > 0) {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg.sender === 'jarvis' && !lastMsg.requestId) {
          existingIdx = prev.length - 1;
        }
      }

      if (existingIdx !== -1) {
        const target = prev[existingIdx];
        const logReqId = reqKey || target.requestId || 'unknown';
        console.log(`[CHAT_MESSAGE_UPDATE] request_id=${logReqId} message_id=${target.id}`);

        let updatedText = target.text;
        if (data.isFinal || data.full_text) {
          updatedText = incomingText.length >= target.text.length ? incomingText : target.text;
        } else if (data.isChunk || data.isSpoken) {
          if (!target.text) {
            updatedText = incomingText;
          } else if (target.text.includes(incomingText) || target.text.endsWith(incomingText)) {
            updatedText = target.text;
          } else {
            updatedText = `${target.text} ${incomingText}`.trim();
          }
        } else {
          updatedText = incomingText.length >= target.text.length ? incomingText : target.text;
        }

        const updated = [...prev];
        updated[existingIdx] = {
          ...target,
          text: updatedText,
          requestId: target.requestId || reqKey || undefined,
          isSpoken: target.isSpoken || !!data.isSpoken,
        };
        return updated;
      }

      const msgId = reqKey || `resp_${Date.now()}`;
      const logReqId = reqKey || 'unknown';
      console.log(`[CHAT_MESSAGE_CREATE] request_id=${logReqId} message_id=${msgId}`);

      return [
        ...prev,
        {
          id: msgId,
          requestId: reqKey || undefined,
          sender: 'jarvis',
          text: incomingText,
          timestamp: data.timestamp || new Date().toISOString(),
          isSpoken: !!data.isSpoken,
        },
      ];
    });
  }, [activeRequestId]);

  // 1. Health Check Poller (FastAPI 8000)
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) {
          const data = await res.json();
          setBackendHealth(data.status === 'ok');
        } else {
          setBackendHealth(false);
        }
      } catch (err) {
        setBackendHealth(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. WebSocket Channel Connection (`ws://localhost:8000/ws/jarvis`)
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/jarvis');

      ws.onopen = () => {
        setWsConnected(true);
        console.log('[WebSocket]: Connected to JARVIS core ws://localhost:8000/ws/jarvis');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const eventType = data.type || data.event;

          if (eventType === 'execution_start') {
            setActiveRequestId(data.request_id || null);
            setCurrentTask(data.task || 'Executing command');
            setActiveStage(data.stage || 'PLANNING');
            setJarvisState('EXECUTING');
            setHasError(false);
            setErrorMessage(null);
          } else if (eventType === 'progress') {
            if (data.request_id) setActiveRequestId(data.request_id);
            if (data.stage) setActiveStage(data.stage);
            setJarvisState('EXECUTING');

            setProgressEvents((prev) => [
              ...prev,
              {
                stage: data.stage || 'EXECUTION',
                text: data.text,
                speak: !!data.speak,
                timestamp: data.timestamp || new Date().isoformat(),
                request_id: data.request_id,
              },
            ]);
          } else if (eventType === 'response_chunk') {
            if (data.text) {
              upsertJarvisMessage({
                request_id: data.request_id,
                text: data.text,
                isChunk: true,
              });
            }
          } else if (eventType === 'speaking_start') {
            setJarvisState('SPEAKING');
            setIsSpeaking(true);

            if (data.text || data.text_display) {
              // Prefer text_display (original with emoji) for the chat bubble.
              // text is the TTS-clean version (no emoji) — only used for audio.
              const displayText = data.text_display || data.text;
              upsertJarvisMessage({
                request_id: data.request_id,
                speech_id: data.speech_id,
                text: displayText,
                timestamp: data.timestamp,
                isSpoken: true,
                isChunk: true,
              });
            }

            if (data.audio_url && !isMuted) {
              if (!enqueuedAudioUrlsRef.current.has(data.audio_url)) {
                enqueuedAudioUrlsRef.current.add(data.audio_url);
                enqueueAudio(data.audio_url);
              }
            }
          } else if (eventType === 'speaking_end') {
            setJarvisState('IDLE');
            setIsSpeaking(false);
          } else if (eventType === 'chat_response' || eventType === 'response_end') {
            const respText = data.text || data.full_text;
            if (respText) {
              upsertJarvisMessage({
                request_id: data.request_id,
                text: respText,
                full_text: data.full_text,
                timestamp: data.timestamp,
                isFinal: true,
              });
            }
          } else if (eventType === 'execution_complete') {
            setActiveStage('COMPLETED');
            setJarvisState('IDLE');
          } else if (eventType === 'error' || eventType === 'chat_error') {
            setHasError(true);
            const errText = data.error?.message || data.message || 'Execution error';
            setErrorMessage(errText);
            setJarvisState('ERROR');
          }
        } catch (e) {
          console.warn('[WebSocket]: Message parse notice', e);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.log('[WebSocket]: Connection closed. Reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        setWsConnected(false);
        console.warn('[WebSocket]: Error encountered', err);
      };

      wsRef.current = ws;
    } catch (err) {
      setWsConnected(false);
      setTimeout(connectWebSocket, 3000);
    }
  }, [isMuted]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Audio Queue Management
  const enqueueAudio = (url: string) => {
    audioQueueRef.current.push(url);
    processNextAudio();
  };

  const processNextAudio = () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    isPlayingRef.current = true;
    const nextUrl = audioQueueRef.current.shift() || null;
    console.log(`[SPEECH_PLAYBACK_START] count=1 url=${nextUrl}`);
    setCurrentAudioUrl(nextUrl);
  };

  const handleAudioEnded = () => {
    console.log(`[SPEECH_PLAYBACK_END] count=1`);
    isPlayingRef.current = false;
    setCurrentAudioUrl(null);
    if (audioQueueRef.current.length > 0) {
      processNextAudio();
    } else {
      setIsSpeaking(false);
      setJarvisState('IDLE');
    }
  };

  // User Action Handlers
  const handleSendMessage = (text: string) => {
    const userMsgId = `user_${Date.now()}`;
    const reqId = `req_${Date.now()}`;
    // Clear previous activeRequestId FIRST to prevent stale ID from matching new response
    setActiveRequestId(null);
    setActiveRequestId(reqId);
    enqueuedAudioUrlsRef.current.clear();

    setChatMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: text,
        timestamp: new Date().toISOString(),
      },
    ]);

    setJarvisState('THINKING');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'chat_command',
          source: 'chat',
          text: text,
          request_id: reqId,
          enable_audio_tts: true,
        })
      );
    } else {
      // Fallback REST call
      fetch('http://localhost:8000/api/v1/jarvis/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, enable_audio_tts: true }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.text) {
            upsertJarvisMessage({
              request_id: reqId,
              text: data.text,
            });
            setJarvisState('IDLE');
          }
        })
        .catch((err) => {
          setHasError(true);
          setErrorMessage('API request failed');
          setJarvisState('ERROR');
        });
    }
  };

  const handleToggleListening = () => {
    const next = !isListening;
    setIsListening(next);
    setJarvisState(next ? 'LISTENING' : 'IDLE');
  };

  const handleTriggerWake = () => {
    handleSendMessage('Jarvis');
  };

  return (
    <div className="bg-slate-950 text-slate-100 font-sans min-h-screen relative flex flex-col overflow-x-hidden selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Sticky Header */}
      <Header
        jarvisState={jarvisState}
        backendHealth={backendHealth}
        wsConnected={wsConnected}
        isMuted={isMuted}
        onToggleMute={() => setIsMuted(!isMuted)}
        onTriggerWake={handleTriggerWake}
      />

      {/* Main Content Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Top Grid: Avatar Core + Execution Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <AvatarCore
              jarvisState={jarvisState}
              isSpeaking={isSpeaking}
              isListening={isListening}
            />
          </div>
          <div className="lg:col-span-7">
            <ExecutionPanel
              requestId={activeRequestId}
              currentTask={currentTask}
              activeStage={activeStage}
              progressEvents={progressEvents}
              hasError={hasError}
              errorMessage={errorMessage}
            />
          </div>
        </div>

        {/* Middle Grid: Chat Panel + Capabilities Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7">
            <ChatPanel
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              isListening={isListening}
              onToggleListening={handleToggleListening}
            />
          </div>
          <div className="lg:col-span-5">
            <CapabilitiesGrid onSelectCommand={handleSendMessage} />
          </div>
        </div>
      </main>

      {/* HTML5 Audio Player Engine */}
      <AudioEngine
        audioUrl={currentAudioUrl}
        isMuted={isMuted}
        onAudioStarted={() => setIsSpeaking(true)}
        onAudioEnded={handleAudioEnded}
      />
    </div>
  );
};

export default App;
