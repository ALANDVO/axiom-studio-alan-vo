/**
 * Typed HTTP API client communicating with FastAPI backend.
 */
import {
  ActionItem,
  ActionReceipt,
  AdvisoryResponse,
  AnomalyScore,
  Bookmark,
  BookmarkCreate,
  CameraFeed,
  HealthResponse,
  MacroCandidate,
  MacroExecuteResult,
  MLBenchmarkResponse,
  SpatialEntity,
  UserProfile,
  WorkflowMacro,
} from '../types';
import { authService } from './auth';

class ApiClient {
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers || {});
    headers.set('Content-Type', 'application/json');

    const token = authService.getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    const response = await fetch(path, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          detail = errorJson.detail;
        }
      } catch {
        // Fallback to HTTP status text
      }
      throw new Error(detail);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Service health and version metadata
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  // Auth endpoints
  async getProfile(): Promise<UserProfile> {
    return this.request<UserProfile>('/api/auth/me');
  }

  // Spatial Intelligence & Telemetry
  async getEntities(params?: {
    min_lat?: number;
    max_lat?: number;
    min_lon?: number;
    max_lon?: number;
    layers?: string[];
    limit?: number;
  }): Promise<SpatialEntity[]> {
    const query = new URLSearchParams();
    if (params?.min_lat !== undefined) query.set('min_lat', params.min_lat.toString());
    if (params?.max_lat !== undefined) query.set('max_lat', params.max_lat.toString());
    if (params?.min_lon !== undefined) query.set('min_lon', params.min_lon.toString());
    if (params?.max_lon !== undefined) query.set('max_lon', params.max_lon.toString());
    if (params?.limit !== undefined) query.set('limit', params.limit.toString());
    if (params?.layers) {
      params.layers.forEach((l) => query.append('layers', l));
    }
    const qs = query.toString();
    return this.request<SpatialEntity[]>(`/api/spatial/entities${qs ? `?${qs}` : ''}`);
  }

  async getCameras(params?: {
    min_lat?: number;
    max_lat?: number;
    min_lon?: number;
    max_lon?: number;
  }): Promise<CameraFeed[]> {
    const query = new URLSearchParams();
    if (params?.min_lat !== undefined) query.set('min_lat', params.min_lat.toString());
    if (params?.max_lat !== undefined) query.set('max_lat', params.max_lat.toString());
    if (params?.min_lon !== undefined) query.set('min_lon', params.min_lon.toString());
    if (params?.max_lon !== undefined) query.set('max_lon', params.max_lon.toString());
    const qs = query.toString();
    return this.request<CameraFeed[]>(`/api/spatial/cameras${qs ? `?${qs}` : ''}`);
  }

  // Bookmarks (Issue #335)
  async getBookmarks(): Promise<Bookmark[]> {
    return this.request<Bookmark[]>('/api/spatial/bookmarks');
  }

  async createBookmark(bookmark: BookmarkCreate): Promise<Bookmark> {
    return this.request<Bookmark>('/api/spatial/bookmarks', {
      method: 'POST',
      body: JSON.stringify(bookmark),
    });
  }

  async deleteBookmark(bookmarkId: string): Promise<void> {
    return this.request<void>(`/api/spatial/bookmarks/${bookmarkId}`, {
      method: 'DELETE',
    });
  }

  // Machine Learning & Anomaly Evaluation
  async detectAnomalies(threshold: number = 0.65, entityIds?: string[]): Promise<AnomalyScore[]> {
    return this.request<AnomalyScore[]>('/api/ml/detect-anomalies', {
      method: 'POST',
      body: JSON.stringify({ threshold, entity_ids: entityIds }),
    });
  }

  async getMLBenchmark(threshold: number = 0.65): Promise<MLBenchmarkResponse> {
    return this.request<MLBenchmarkResponse>(`/api/ml/benchmark?threshold=${threshold}`);
  }

  async requestAdvisory(
    query: string,
    opts?: { target_entity_id?: string; include_sensor_context?: boolean },
  ): Promise<AdvisoryResponse> {
    return this.request<AdvisoryResponse>('/api/ml/advisory', {
      method: 'POST',
      body: JSON.stringify({
        query,
        target_entity_id: opts?.target_entity_id,
        include_sensor_context: opts?.include_sensor_context,
      }),
    });
  }

  // Workflow Macros (Issue #824)
  async recordActionReceipt(receipt: ActionReceipt): Promise<void> {
    await this.request<void>('/api/macros/receipts', {
      method: 'POST',
      body: JSON.stringify(receipt),
    });
  }

  async getMacroCandidates(minSupport: number = 2): Promise<MacroCandidate[]> {
    return this.request<MacroCandidate[]>(`/api/macros/candidates?min_support=${minSupport}`);
  }

  async confirmMacro(name: string, description: string, triggerContext: string, actions: ActionItem[]): Promise<WorkflowMacro> {
    return this.request<WorkflowMacro>('/api/macros/confirm', {
      method: 'POST',
      body: JSON.stringify({
        name,
        description,
        trigger_context: triggerContext,
        actions,
      }),
    });
  }

  async getMacros(): Promise<WorkflowMacro[]> {
    return this.request<WorkflowMacro[]>('/api/macros');
  }

  async executeMacro(macroId: string): Promise<MacroExecuteResult> {
    return this.request<MacroExecuteResult>(`/api/macros/${macroId}/execute`, {
      method: 'POST',
    });
  }

  async demoteMacro(macroId: string, reason: string): Promise<WorkflowMacro> {
    return this.request<WorkflowMacro>(`/api/macros/${macroId}/demote?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
