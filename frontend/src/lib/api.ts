const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface PipelineRun {
  run_id: string;
  branch: string;
  commit_sha: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  triggered_at: string;
  completed_at?: string;
  duration_seconds?: number;
  transport_id?: string;
}

export interface TransportRecord {
  id: string;
  transport_id: string;
  description: string;
  source_system: string;
  target_system: string;
  status: 'pending' | 'in_progress' | 'success' | 'failed';
  promoted_by: string;
  promoted_at: string;
  completed_at?: string;
  validation_report?: any;
}

export interface SystemHealth {
  cpu_percent: number;
  memory_percent: number;
  active_users: number;
  avg_response_ms: number;
  status: 'healthy' | 'degraded' | 'down';
}

export interface PipelineMetrics {
  date: string;
  success: number;
  failed: number;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getPipelineStatus(): Promise<{ current_status: string; last_runs: PipelineRun[] }> {
    return this.request('/pipeline/status');
  }

  async getPipelineRun(runId: string): Promise<PipelineRun> {
    return this.request(`/pipeline/runs/${runId}`);
  }

  async triggerPipeline(branch: string = 'main'): Promise<{ message: string; branch: string }> {
    return this.request(`/pipeline/trigger?branch=${branch}`, {
      method: 'POST',
    });
  }

  async getPipelineMetrics(): Promise<PipelineMetrics[]> {
    return this.request('/pipeline/metrics');
  }

  async getActiveTransports(): Promise<{ transports: any[] }> {
    return this.request('/transport/active');
  }

  async getTransportHistory(): Promise<{ transports: TransportRecord[] }> {
    return this.request('/transport/history');
  }

  async promoteTransport(
    transportId: string,
    sourceSystem: string,
    targetSystem: string,
    promotedBy: string
  ): Promise<any> {
    return this.request('/transport/promote', {
      method: 'POST',
      body: JSON.stringify({
        transport_id: transportId,
        source_system: sourceSystem,
        target_system: targetSystem,
        promoted_by: promotedBy,
      }),
    });
  }

  async getTransportDetails(transportId: string): Promise<TransportRecord> {
    return this.request(`/transport/${transportId}`);
  }

  async validateTransport(transportId: string): Promise<any> {
    return this.request(`/transport/validate?transport_id=${transportId}`, {
      method: 'POST',
    });
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.request('/health/system');
  }

  async getHealthHistory(limit: number = 50): Promise<any[]> {
    return this.request(`/health/history?limit=${limit}`);
  }
}

export const api = new APIClient();
