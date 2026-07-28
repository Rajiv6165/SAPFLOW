'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

export interface PipelineRun {
  run_id: string;
  branch: string;
  commit_sha: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  triggered_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  transport_id?: string;
}


export interface PipelineEvent {
  event_type: string;
  message: string;
  timestamp: string;
  transport_id?: string;
}

export interface WebSocketPayload {
  type?: string;
  timestamp?: string;
  runs?: PipelineRun[];
  metrics?: {
    total_runs: number;
    success_count: number;
    failed_count: number;
    running_count: number;
    success_rate: number;
    active_transports: number;
  };
  summary?: any;
  events?: any[];
  recent_events?: PipelineEvent[];
  recent_runs?: PipelineRun[];
  run_id?: string;
  branch?: string;
  commit_sha?: string;
  duration_seconds?: number;
  transport_id?: string;
  status?: string;
  [key: string]: any;
}

export type PipelineData = WebSocketPayload;

const DEFAULT_WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/pipeline';

export function useWebSocket(url: string = DEFAULT_WS_URL) {
  const [data, setData] = useState<WebSocketPayload | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        return;
      }

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
          if (message.type === 'pipeline_update' || message.runs || message.summary) {
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

export const usePipelineWebSocket = useWebSocket;
