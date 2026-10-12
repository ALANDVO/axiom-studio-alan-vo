import React, { useState } from 'react';
import { AdvisoryResponse, MacroCandidate, WorkflowMacro } from '../types';
import { Sparkles, Zap, Bot } from 'lucide-react';

interface MacroAssistantProps {
  candidates: MacroCandidate[];
  macros: WorkflowMacro[];
  onConfirmMacro: (candidate: MacroCandidate, customName?: string) => Promise<void>;
  onExecuteMacro: (macroId: string) => Promise<void>;
  onAskAdvisory: (query: string) => Promise<AdvisoryResponse>;
  canManage: boolean;
}

export const MacroAssistant: React.FC<MacroAssistantProps> = ({
  candidates,
  macros,
  onConfirmMacro,
  onExecuteMacro,
  onAskAdvisory,
  canManage,
}) => {
  const [query, setQuery] = useState<string>('');
  const [advisoryResult, setAdvisoryResult] = useState<AdvisoryResponse | null>(null);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsAsking(true);
    setStatusMsg(null);
    try {
      const res = await onAskAdvisory(query.trim());
      setAdvisoryResult(res);
      setQuery('');
    } catch (err: any) {
      setStatusMsg(err.message || 'Advisory request failed');
    } finally {
      setIsAsking(false);
    }
  };

  const handleExecute = async (id: string) => {
    setExecutingId(id);
    setStatusMsg(null);
    try {
      await onExecuteMacro(id);
      setStatusMsg('Macro executed successfully with verified state check.');
    } catch (err: any) {
      setStatusMsg(err.message || 'Macro execution failed.');
    } finally {
      setExecutingId(null);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 shadow h-full">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center space-x-2 text-slate-100">
          <Zap className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold tracking-wide">WORKFLOW MACROS & ADVISORY (ISSUE #824)</h2>
        </div>
      </div>

      {/* Routine Candidate Detection (Issue #824 Slice 2 & 3) */}
      {candidates.length > 0 && canManage && (
        <div className="p-3 bg-amber-950/30 border border-amber-800/80 rounded-lg text-xs font-mono space-y-2">
          <div className="flex items-center space-x-1.5 text-amber-300 font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Detected Repeated Workflow Candidate:</span>
          </div>
          {candidates.map((cand, idx) => (
            <div key={idx} className="flex items-center justify-between bg-slate-950/70 p-2 rounded">
              <div>
                <div className="text-slate-200 font-medium">{cand.suggested_name}</div>
                <div className="text-[10px] text-slate-500">
                  Support: {cand.frequency_count} repeats • Success: {(cand.verified_success_rate * 100).toFixed(0)}%
                </div>
              </div>
              <button
                onClick={() => onConfirmMacro(cand)}
                className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-[11px] font-medium transition"
              >
                Save Shortcut
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Active Compiled Macros List */}
      <div className="space-y-1.5">
        <span className="text-xs text-slate-400 font-semibold tracking-wider">COMPILED ROUTINES:</span>
        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
          {macros.length === 0 ? (
            <div className="text-xs text-slate-500 font-mono py-2">
              No compiled shortcuts yet. Execute repeated actions on the globe to detect routines.
            </div>
          ) : (
            macros.map((m) => (
              <div
                key={m.id}
                className={`p-2 rounded border text-xs font-mono flex items-center justify-between ${
                  m.status === 'demoted'
                    ? 'bg-slate-950/50 border-slate-800 text-slate-500'
                    : 'bg-slate-950 border-slate-800 text-slate-300'
                }`}
              >
                <div>
                  <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                    <span>{m.name}</span>
                    {m.status === 'demoted' && (
                      <span className="text-[9px] px-1 bg-rose-950 text-rose-400 border border-rose-800 rounded">
                        DEMOTED
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {m.actions.map((a) => a.name).join(' → ')}
                  </div>
                </div>

                {canManage && m.status === 'active' && (
                  <button
                    onClick={() => handleExecute(m.id)}
                    disabled={executingId === m.id}
                    className="px-2 py-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white rounded text-[10px] font-medium transition flex items-center space-x-1"
                  >
                    <span>{executingId === m.id ? 'Running...' : 'Run'}</span>
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {statusMsg && <div className="text-xs font-mono text-emerald-400">{statusMsg}</div>}

      {/* Opt-in Advisory AI Assistant */}
      <div className="border-t border-slate-800 pt-2 flex flex-col gap-2">
        <div className="flex items-center space-x-1.5 text-xs text-slate-300">
          <Bot className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-medium">Advisory Assistant (Multi-Provider Grounded)</span>
        </div>

        <form onSubmit={handleAsk} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask question about active satellites, cameras or airspace..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-100 focus:outline-none focus:border-sky-500 font-mono"
          />
          <button
            type="submit"
            disabled={isAsking || !query.trim()}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-sky-400 rounded text-xs font-medium transition"
          >
            {isAsking ? 'Thinking...' : 'Ask'}
          </button>
        </form>

        {advisoryResult && (
          <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono space-y-1">
            <div className="text-[10px] text-slate-500 flex justify-between">
              <span>PROVIDER: {advisoryResult.provider_used}</span>
              <span>CONFIDENCE: {(advisoryResult.confidence * 100).toFixed(0)}%</span>
            </div>
            <p className="text-slate-300 whitespace-pre-wrap">{advisoryResult.summary}</p>
            <div className="text-[9px] text-slate-600 italic mt-1">{advisoryResult.disclaimer}</div>
          </div>
        )}
      </div>
    </div>
  );
};
