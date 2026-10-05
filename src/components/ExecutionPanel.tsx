import React from 'react';
import { Terminal, CheckCircle2, Clock, AlertCircle, Layers } from 'lucide-react';

export interface ProgressEventItem {
  stage: string;
  text: string;
  speak: boolean;
  timestamp: string;
  request_id?: string;
}

interface ExecutionPanelProps {
  requestId: string | null;
  currentTask: string | null;
  activeStage: string;
  progressEvents: ProgressEventItem[];
  hasError: boolean;
  errorMessage: string | null;
}

export const ExecutionPanel: React.FC<ExecutionPanelProps> = ({
  requestId,
  currentTask,
  activeStage,
  progressEvents,
  hasError,
  errorMessage,
}) => {
  const stages = [
    { id: 'PLANNING', label: '1. Planning' },
    { id: 'FILE_CREATE', label: '2. File Gen' },
    { id: 'API_BUILD', label: '3. Build' },
    { id: 'TESTING', label: '4. Verify' },
    { id: 'COMPLETED', label: '5. Complete' },
  ];

  const getStageIndex = (stageId: string) => {
    const s = stageId.toUpperCase();
    if (s === 'PLANNING' || s === 'INIT') return 0;
    if (s.includes('FILE') || s.includes('CODE') || s.includes('GENERAT')) return 1;
    if (s.includes('BUILD') || s.includes('DEP')) return 2;
    if (s.includes('TEST') || s.includes('VALIDAT') || s.includes('PREVIEW')) return 3;
    if (s.includes('COMPLETE')) return 4;
    return 1;
  };

  const currentStageIndex = getStageIndex(activeStage);

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-col h-full shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-emerald-400" />
          <h2 className="text-sm font-bold font-mono text-white tracking-wide">
            REAL-TIME EXECUTION TRACKER
          </h2>
        </div>
        {requestId && (
          <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-400">
            ID: <span className="text-cyan-400 font-semibold">{requestId}</span>
          </span>
        )}
      </div>

      {/* Task Summary Banner */}
      <div className="mb-4 bg-slate-900/90 border border-slate-800 rounded-xl p-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
          <span className="flex items-center gap-1.5 text-slate-300">
            <Layers className="w-3.5 h-3.5 text-cyan-400" /> ACTIVE TASK:
          </span>
          <span className="text-emerald-400 font-semibold">{activeStage || 'IDLE'}</span>
        </div>
        <p className="text-xs font-sans text-slate-200 font-medium truncate">
          {currentTask || 'No active background task running.'}
        </p>
      </div>

      {/* Pipeline Stage Timeline Bar */}
      <div className="mb-4 grid grid-cols-5 gap-1.5">
        {stages.map((st, idx) => {
          const isDone = idx < currentStageIndex || activeStage === 'COMPLETED';
          const isCurrent = idx === currentStageIndex && activeStage !== 'COMPLETED' && !hasError;
          const isFailed = hasError && idx === currentStageIndex;

          return (
            <div
              key={st.id}
              className={`flex flex-col items-center justify-center p-2 rounded-lg text-[10px] font-mono border transition-all ${
                isDone
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                  : isCurrent
                  ? 'bg-cyan-950/60 border-cyan-400 text-cyan-200 animate-pulse shadow-sm shadow-cyan-500/20'
                  : isFailed
                  ? 'bg-rose-950/60 border-rose-500 text-rose-300'
                  : 'bg-slate-900/50 border-slate-800 text-slate-500'
              }`}
            >
              {isDone ? (
                <CheckCircle2 className="w-3.5 h-3.5 mb-1 text-emerald-400" />
              ) : isFailed ? (
                <AlertCircle className="w-3.5 h-3.5 mb-1 text-rose-400" />
              ) : (
                <Clock className="w-3.5 h-3.5 mb-1 opacity-60" />
              )}
              <span className="truncate w-full text-center">{st.label}</span>
            </div>
          );
        })}
      </div>

      {/* Real-time Progress Events Log Stream */}
      <div className="flex-1 bg-slate-950/90 border border-slate-800/80 rounded-xl p-3 overflow-y-auto max-h-[220px] font-mono text-xs space-y-2">
        {progressEvents.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-xs italic">
            Waiting for execution telemetry events...
          </div>
        ) : (
          progressEvents.map((evt, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 border-b border-slate-900 pb-1.5 last:border-0 last:pb-0"
            >
              <span className="text-[10px] text-slate-500 whitespace-nowrap pt-0.5">
                {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : ''}
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 whitespace-nowrap">
                [{evt.stage}]
              </span>
              <span className="text-slate-200 flex-1 leading-relaxed">{evt.text}</span>
            </div>
          ))
        )}

        {hasError && errorMessage && (
          <div className="p-2 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
};
