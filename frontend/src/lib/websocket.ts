import { useEffect, useState, useRef, useCallback } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/pipeline';

export interface PipelineData {
  id?: string;
  run_id: string;
  branch: string;
  commit_sha: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  triggered_at: string;
  duration_seconds?: number;
  transport_id?: string;
}

export interface WebSocketPayload {
  type: string;
  timestamp: string;
  summary: {
    total_runs_today: number;
    success_rate: number;
    active_transports: number;
    system_status: 'healthy' | 'degraded' | 'down' | 'unknown';
  };
  recent_runs: PipelineData[];
}

export function usePipelineWebSocket(url: string = WS_URL) {
  const [data, setData] = useState<WebSocketPayload | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        setReconnectCount(0);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketPayload = JSON.parse(event.data);
          if (message.type === 'pipeline_update') {
            setData(message);
            setLastUpdated(new Date());
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttemptsRef.current) * 1000;
          reconnectAttemptsRef.current++;
          setReconnectCount(reconnectAttemptsRef.current);
          console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectAttemptsRef.current})`);
          setTimeout(connect, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { data, isConnected, lastUpdated, reconnectCount };
}
