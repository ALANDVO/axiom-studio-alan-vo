import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BookmarksTray } from '../components/BookmarksTray';
import { AnomalyConsole } from '../components/AnomalyConsole';
import { MacroAssistant } from '../components/MacroAssistant';
import { AdvisoryResponse, Bookmark, MLBenchmarkResponse } from '../types';

describe('User-visible workflows and components', () => {
  it('renders favourite bookmarks tray and triggers fly-to callback (Issue #335)', () => {
    const mockBookmarks: Bookmark[] = [
      {
        id: 'bm-1',
        name: 'Austin Hub',
        latitude: 30.2672,
        longitude: -97.7431,
        altitude: 1000,
        heading: 0,
        pitch: -45,
        active_layers: ['satellites'],
        created_by: 'analyst',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];

    const onSelect = vi.fn();
    const onSave = vi.fn().mockResolvedValue(undefined);
    const onDelete = vi.fn().mockResolvedValue(undefined);

    render(
      <BookmarksTray
        bookmarks={mockBookmarks}
        onSelectBookmark={onSelect}
        onSaveBookmark={onSave}
        onDeleteBookmark={onDelete}
        canSave={true}
      />
    );

    expect(screen.getByText('Austin Hub')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Austin Hub'));
    expect(onSelect).toHaveBeenCalledWith(mockBookmarks[0]);
  });

  it('renders ML anomaly console and toggles benchmark evaluation metrics', () => {
    const mockBenchmark: MLBenchmarkResponse = {
      dataset_name: 'Test Dataset',
      dataset_size: 20,
      evaluated_at: new Date().toISOString(),
      baseline_algorithm: 'Static Baseline',
      model_algorithm: 'Kinematic Z-Score Classifier',
      metrics: {
        precision: 0.95,
        recall: 0.90,
        f1_score: 0.925,
        accuracy: 0.93,
        false_positive_rate: 0.05,
        roc_auc: 0.98,
        evaluation_samples: 20,
        mean_inference_latency_ms: 0.05,
      },
      confusion_matrix: {
        true_positives: 9,
        false_positives: 1,
        true_negatives: 10,
        false_negatives: 0,
      },
      failure_cases: [],
    };

    render(
      <AnomalyConsole
        anomalies={[]}
        benchmark={mockBenchmark}
        onRunScan={vi.fn().mockResolvedValue(undefined)}
        onRunBenchmark={vi.fn().mockResolvedValue(undefined)}
        isScanning={false}
        canScan={true}
      />
    );

    expect(screen.getByText(/AI\/ML TRAJECTORY ANOMALY ENGINE/i)).toBeInTheDocument();
    // Switch to Benchmark tab
    fireEvent.click(screen.getByText('ML Benchmark'));
    expect(screen.getByText('PRECISION')).toBeInTheDocument();
    expect(screen.getByText('95.0%')).toBeInTheDocument();
  });

  it('renders workflow macro assistant with detected candidates (Issue #824)', () => {
    const candidates = [
      {
        context_fingerprint: 'viewport-layers',
        actions: [{ name: 'toggle_layer', args: { layer: 'satellites' } }],
        frequency_count: 3,
        verified_success_rate: 1.0,
        suggested_name: 'Workflow: toggle_layer',
      },
    ];

    const onConfirm = vi.fn().mockResolvedValue(undefined);

    render(
      <MacroAssistant
        candidates={candidates}
        macros={[]}
        onConfirmMacro={onConfirm}
        onExecuteMacro={vi.fn().mockResolvedValue(undefined)}
        onAskAdvisory={vi.fn().mockResolvedValue({} as AdvisoryResponse)}
        canManage={true}
      />
    );

    expect(screen.getByText(/Workflow: toggle_layer/i)).toBeInTheDocument();
    const saveButton = screen.getByRole('button', { name: /Save Shortcut/i });
    fireEvent.click(saveButton);
    expect(onConfirm).toHaveBeenCalledWith(candidates[0]);
  });
});
