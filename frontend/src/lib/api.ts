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

const BASE_URL = API_URL;

const safeFetch = async <T>(url: string, options?: RequestInit): Promise<T | null> => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!response.ok) {
      console.warn(`Fetch returned status ${response.status} for ${url}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`Fetch error for ${url}:`, error);
    return null;
  }
};

export const api = {
  getPipelineRuns: () => safeFetch<any>(`${BASE_URL}/pipeline/status`),
  getPipelineStatus: () => safeFetch<any>(`${BASE_URL}/pipeline/status`),
  getPipelineMetrics: () => safeFetch<PipelineMetrics[]>(`${BASE_URL}/pipeline/metrics`),
  getActiveTransports: () => safeFetch<{ transports: any[] }>(`${BASE_URL}/transport/active`),
  getTransportHistory: () => safeFetch<{ transports: TransportRecord[] }>(`${BASE_URL}/transport/history`),
  promoteTransport: (...args: any[]) => {
    let bodyData;
    if (args.length === 1 && typeof args[0] === 'object') {
      bodyData = args[0];
    } else {
      bodyData = {
        transport_id: args[0],
        source_system: args[1],
        target_system: args[2],
        promoted_by: args[3] || 'manual',
      };
    }
    return safeFetch<any>(`${BASE_URL}/transport/promote`, {
      method: 'POST',
      body: JSON.stringify(bodyData),
    });
  },
  getSystemHealth: () => safeFetch<SystemHealth>(`${BASE_URL}/health/system`),
  getHealthHistory: (limit?: number) => {
    const url = limit ? `${BASE_URL}/health/history?limit=${limit}` : `${BASE_URL}/health/history`;
    return safeFetch<any[]>(url);
  },
  getTransportDetails: (transportId: string) => safeFetch<TransportRecord>(`${BASE_URL}/transport/${transportId}`),
  validateTransport: (transportId: string) => safeFetch<any>(`${BASE_URL}/transport/validate?transport_id=${transportId}`, {
    method: 'POST',
  }),
};
