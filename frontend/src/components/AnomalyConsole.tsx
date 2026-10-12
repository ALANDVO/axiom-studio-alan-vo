import React, { useState } from 'react';
import { AnomalyScore, MLBenchmarkResponse } from '../types';
import { Activity, BarChart2, Play } from 'lucide-react';

interface AnomalyConsoleProps {
  anomalies: AnomalyScore[];
  benchmark: MLBenchmarkResponse | null;
  onRunScan: () => Promise<void>;
  onRunBenchmark: () => Promise<void>;
  isScanning: boolean;
  canScan: boolean;
}

export const AnomalyConsole: React.FC<AnomalyConsoleProps> = ({
  anomalies,
  benchmark,
  onRunScan,
  onRunBenchmark,
  isScanning,
  canScan,
}) => {
  const [activeTab, setActiveTab] = useState<'scan' | 'benchmark'>('scan');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 shadow h-full">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center space-x-2 text-slate-100">
          <Activity className="w-4 h-4 text-rose-400" />
          <h2 className="text-sm font-semibold tracking-wide">AI/ML TRAJECTORY ANOMALY ENGINE</h2>
        </div>

        <div className="flex space-x-1 bg-slate-950 p-0.5 rounded border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab('scan')}
            className={`px-2.5 py-1 rounded transition ${
              activeTab === 'scan' ? 'bg-slate-800 text-sky-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Live Scan ({anomalies.filter((a) => a.is_anomalous).length})
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`px-2.5 py-1 rounded transition ${
              activeTab === 'benchmark' ? 'bg-slate-800 text-sky-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ML Benchmark
          </button>
        </div>
      </div>

      {activeTab === 'scan' ? (
        <div className="flex flex-col gap-3 flex-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Scans orbital maneuvers, rapid dives, and transponder spoofing.
            </span>
            {canScan && (
              <button
                onClick={onRunScan}
                disabled={isScanning}
                className="flex items-center space-x-1 px-3 py-1 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded text-xs font-medium transition"
              >
                <Play className={`w-3 h-3 ${isScanning ? 'animate-spin' : ''}`} />
                <span>{isScanning ? 'Analyzing...' : 'Execute Scan'}</span>
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto max-h-56 space-y-2 pr-1">
            {anomalies.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-500 font-mono">
                No active scan performed. Click 'Execute Scan' to run kinematic ML model.
              </div>
            ) : (
              anomalies.map((anom) => (
                <div
                  key={anom.entity_id}
                  className={`p-2.5 rounded-lg border text-xs font-mono flex flex-col gap-1 ${
                    anom.is_anomalous
                      ? 'bg-rose-950/30 border-rose-800/80 text-rose-200'
                      : 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-100">{anom.entity_id}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        anom.is_anomalous ? 'bg-rose-900 text-rose-300' : 'bg-emerald-950 text-emerald-400'
                      }`}
                    >
                      SCORE: {(anom.anomaly_score * 100).toFixed(0)}%
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400">{anom.explanation}</p>

                  {anom.detected_patterns.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {anom.detected_patterns.map((pat, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.5 bg-rose-950 text-rose-300 rounded border border-rose-800 text-[9px]"
                        >
                          {pat}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3 flex-1 text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Ground-truth kinematic test dataset:</span>
            <button
              onClick={onRunBenchmark}
              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs transition flex items-center space-x-1"
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Re-run Evaluation</span>
            </button>
          </div>

          {benchmark ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500">PRECISION</div>
                  <div className="text-sm font-bold text-sky-400">
                    {(benchmark.metrics.precision * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500">RECALL</div>
                  <div className="text-sm font-bold text-emerald-400">
                    {(benchmark.metrics.recall * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500">F1-SCORE</div>
                  <div className="text-sm font-bold text-purple-400">
                    {benchmark.metrics.f1_score.toFixed(3)}
                  </div>
                </div>
              </div>

              <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[11px] space-y-1">
                <div>Model: <span className="text-slate-300">{benchmark.model_algorithm}</span></div>
                <div>Baseline: <span className="text-slate-400">{benchmark.baseline_algorithm}</span></div>
                <div>Samples: <span className="text-slate-300">{benchmark.dataset_size} labeled tracks</span></div>
                <div>Latency: <span className="text-sky-300">{benchmark.metrics.mean_inference_latency_ms.toFixed(3)} ms/sample</span></div>
                <div>ROC-AUC: <span className="text-emerald-300">{benchmark.metrics.roc_auc.toFixed(3)}</span></div>
              </div>

              <div className="p-2 bg-slate-950 rounded border border-slate-800 text-[10px]">
                <div className="text-slate-500 mb-1 font-semibold">CONFUSION MATRIX:</div>
                <div className="grid grid-cols-2 gap-1 text-slate-300">
                  <div>True Positives: {benchmark.confusion_matrix.true_positives}</div>
                  <div>False Positives: {benchmark.confusion_matrix.false_positives}</div>
                  <div>True Negatives: {benchmark.confusion_matrix.true_negatives}</div>
                  <div>False Negatives: {benchmark.confusion_matrix.false_negatives}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-6 text-center text-slate-500 font-mono">
              Loading benchmark metrics...
            </div>
          )}
        </div>
      )}
    </div>
  );
};
