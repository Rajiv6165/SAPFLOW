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

export interface PaginatedTransports {
  items: TransportRecord[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
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
      console.warn(\Fetch returned status \ for \);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(\Fetch error for \:\, error);
    return null;
  }
};

export const api = {
  getPipelineRuns: () => safeFetch<any>(`${BASE_URL}/api/v1/pipeline/status`),
  getPipelineStatus: () => safeFetch<any>(`${BASE_URL}/api/v1/pipeline/status`),
  getPipelineMetrics: () => safeFetch<PipelineMetrics[]>(`${BASE_URL}/api/v1/pipeline/metrics`),
  getActiveTransports: () => safeFetch<{ transports: any[] }>(`${BASE_URL}/api/v1/transport/active`),
  getTransportHistory: (landscape?: string, page: number = 1, limit: number = 20) => {
    const params = new URLSearchParams();
    if (landscape && landscape !== 'all' && landscape.trim() !== '') {
      params.append('landscape', landscape);
    }
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    return safeFetch<PaginatedTransports>(`${BASE_URL}/api/v1/transport/history?${params.toString()}`);
  },

  getLandscapes: () => safeFetch<string[]>(`${BASE_URL}/api/v1/transport/landscapes`),
  getTransportStats: () => safeFetch<any>(`${BASE_URL}/api/v1/transport/stats`),
  rollbackTransport: (transportId: string) => safeFetch<any>(`${BASE_URL}/api/v1/transport/${transportId}/rollback`, {

    method: 'POST'
  }),
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
        landscape: args[4] || 'DEFAULT',
      };
    }
    return safeFetch<any>(\/api/v1/transport/promote\, {
      method: 'POST',
      body: JSON.stringify(bodyData),
    });
  },
  getSystemHealth: () => safeFetch<SystemHealth>(\/api/v1/health/system\),
  getSapConnectionStatus: () => fetch(\/api/v1/health/sap-connection\).then(r => r.json()),
  testSapConnection: () => safeFetch<any>(\/api/v1/health/sap-connection/test\, {
    method: 'POST'
  }),
  getHealthHistory: (limit?: number) => {
    const url = limit ? \/api/v1/health/history?limit=\ : \/api/v1/health/history\;
    return safeFetch<any[]>(url);
  },
  getTransportDetails: (transportId: string) => safeFetch<TransportRecord>(\/api/v1/transport/\),
  validateTransport: (transportId: string) => safeFetch<any>(\/api/v1/transport/validate?transport_id=\, {
    method: 'POST',
  }),
  getRunJobs: (runId: string) => safeFetch<any>(\/api/v1/pipeline/runs/\/jobs\),
  syncPipeline: () => safeFetch<any>(\/api/v1/pipeline/sync\, {
    method: 'POST',
  }),
  triggerPipeline: (branch: string) => safeFetch<any>(\/api/v1/pipeline/trigger\, {
    method: 'POST',
    body: JSON.stringify({ branch }),
  }),
  resetDemoData: () => safeFetch<any>(\/api/v1/demo/reset\, {
    method: 'POST'
  }),
};
