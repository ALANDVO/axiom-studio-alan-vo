/**
 * Typed domain interfaces derived from backend FastAPI models and response envelopes.
 */

export interface CameraPose {
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  pitch: number;
}

export interface Bookmark {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  pitch: number;
  active_layers: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BookmarkCreate {
  name: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  pitch: number;
  active_layers: string[];
}

export interface SpatialEntity {
  id: string;
  entity_type: 'satellite' | 'aircraft' | 'rf_station' | 'camera';
  callsign: string;
  latitude: number;
  longitude: number;
  altitude: number;
  velocity: number;
  heading: number;
  status: string;
  metadata: Record<string, any>;
  last_seen: string;
}

export interface CameraFeed {
  id: string;
  name: string;
  city: string;
  region: string;
  latitude: number;
  longitude: number;
  stream_url: string;
  attribution: string;
  is_healthy: boolean;
  fps: number;
  last_poll_status: string;
  fov_degrees: number;
}

export interface AnomalyScore {
  entity_id: string;
  entity_type: string;
  anomaly_score: number;
  is_anomalous: boolean;
  confidence: number;
  detected_patterns: string[];
  explanation: string;
}

export interface BenchmarkMetric {
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
  false_positive_rate: number;
  roc_auc: number;
  evaluation_samples: number;
  mean_inference_latency_ms: number;
}

export interface MLBenchmarkResponse {
  dataset_name: string;
  dataset_size: number;
  evaluated_at: string;
  baseline_algorithm: string;
  model_algorithm: string;
  metrics: BenchmarkMetric;
  confusion_matrix: {
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
  };
  failure_cases: Array<{
    id: string;
    description: string;
    error_type: string;
    score: number;
    threshold: number;
    patterns: string[];
  }>;
}

export interface ActionItem {
  name: string;
  args: Record<string, any>;
}

export interface ActionReceipt {
  session_id: string;
  context_fingerprint: string;
  action_name: string;
  args: Record<string, any>;
  result_status: string;
  duration_ms: number;
}

export interface MacroCandidate {
  context_fingerprint: string;
  actions: ActionItem[];
  frequency_count: number;
  verified_success_rate: number;
  suggested_name: string;
}

export interface WorkflowMacro {
  id: string;
  name: string;
  description: string;
  trigger_context: string;
  actions: ActionItem[];
  support_count: number;
  verified_success_rate: number;
  status: 'active' | 'demoted';
  created_at: string;
}

export interface MacroExecuteResult {
  macro_id: string;
  executed_actions: number;
  success: boolean;
  results: Array<Record<string, any>>;
  demoted: boolean;
  demotion_reason?: string;
}

export interface AdvisoryResponse {
  query: string;
  summary: string;
  confidence: number;
  provider_used: string;
  grounding_entities: string[];
  disclaimer: string;
}

export interface UserProfile {
  user_id: string;
  username: string;
  email?: string;
  roles: string[];
  is_demo: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  roles: string[];
  username: string;
  is_demo: boolean;
}
