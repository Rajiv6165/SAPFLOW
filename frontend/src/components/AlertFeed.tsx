'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { usePipelineWebSocket } from '@/lib/websocket';

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'success' | 'info';
  rawType: string;
  title: string;
  message: string;
  timestamp: string;
  source: string;
}

const MOCK_ALERTS: Alert[] = [
  {
    id: 'mock-1',
    type: 'error',
    rawType: 'PIPELINE_FAILED',
    title: 'Pipeline Failed',
    message: 'Transport DEVK900001 failed ABAP inspection in QA. Severity: ERROR — 3 findings.',
    timestamp: new Date(Date.now() - 300_000).toISOString(),
    source: 'Branch: develop',
  },
  {
    id: 'mock-2',
    type: 'warning',
    rawType: 'PIPELINE_STARTED',
    title: 'Pipeline Started',
    message: 'SAP system CPU exceeded 90% threshold for 5+ minutes. CloudWatch alarm active.',
    timestamp: new Date(Date.now() - 600_000).toISOString(),
    source: 'Branch: main',
  },
  {
    id: 'mock-3',
    type: 'success',
    rawType: 'TRANSPORT_PROMOTED',
    title: 'Transport Promoted',
    message: 'DEVK900002 successfully imported into QA. 14 objects transported.',
    timestamp: new Date(Date.now() - 900_000).toISOString(),
    source: 'Transport: DEVK900002',
  },
];

const alertConfig = {
  error:   { iconColor: '#ef4444', className: 'alert-error',   label: 'FAIL' },
  warning: { iconColor: '#f59e0b', className: 'alert-warning', label: 'RUN'  },
  success: { iconColor: '#10b981', className: 'alert-success', label: 'OK'    },
  info:    { iconColor: '#3b82f6', className: 'alert-info',    label: 'PUSH'  },
};

function EventIcon({ type, className = 'w-4 h-4' }: { type: string; className?: string }) {
  if (type === 'PUSH') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="#3b82f6">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  );
  if (type === 'PIPELINE_STARTED') return (
    <svg className={`${className} animate-pulse`} fill="none" viewBox="0 0 24 24" stroke="#f59e0b">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
  if (type === 'PIPELINE_PASSED') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="#10b981">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
  if (type === 'PIPELINE_FAILED') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="#ef4444">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
  if (type === 'TRANSPORT_PROMOTED') return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="#10b981">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.354 15.354A9 9 0 018.646 3.646m.146 11.646L21 2.1l-7.243 7.243M18.75 6.25l-2.5 2.5" />
    </svg>
  );
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="#3b82f6">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function formatRelTime(dateString: string): string {
  const diff = Date.now() - new Date(dateString).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return new Date(dateString).toLocaleDateString();
}

export default function AlertFeed() {
  const { data: wsData } = usePipelineWebSocket();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [, forceUpdate] = useState(0);
  const [lastSeenEventId, setLastSeenEventId] = useState<string | null>(null);
  const [flashEventId, setFlashEventId] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getSystemHealth()
      .then((data) => {
        if (data) {
          setError(false);
          if (!wsData?.events) {
            setAlerts(MOCK_ALERTS);
            setLoading(false);
          }
        } else {
          setError(true);
          setLoading(false);
        }
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (wsData?.events) {
      const mappedEvents: Alert[] = wsData.events.map((e: any) => {
        let type: Alert['type'] = 'info';
        let title = '';
        
        switch (e.type) {
          case 'PUSH':
            type = 'info';
            title = 'Commit Pushed';
            break;
          case 'PIPELINE_STARTED':
            type = 'warning';
            title = 'Pipeline Started';
            break;
          case 'PIPELINE_PASSED':
            type = 'success';
            title = 'Pipeline Passed';
            break;
          case 'PIPELINE_FAILED':
            type = 'error';
            title = 'Pipeline Failed';
            break;
          case 'TRANSPORT_PROMOTED':
            type = 'success';
            title = 'Transport Promoted';
            break;
          default:
            type = 'info';
            title = 'System Event';
        }

        return {
          id: e.id,
          type,
          rawType: e.type,
          title,
          message: e.message,
          timestamp: e.timestamp,
          source: e.branch ? `Branch: ${e.branch}` : (e.transport_id ? `Transport: ${e.transport_id}` : 'System'),
        };
      });
      
      if (mappedEvents.length > 0) {
        const newestEventId = mappedEvents[0].id;
        if (lastSeenEventId && newestEventId !== lastSeenEventId) {
          setFlashEventId(newestEventId);
          setTimeout(() => setFlashEventId(null), 2000);
        }
        setLastSeenEventId(newestEventId);
      }
      
      setAlerts(mappedEvents);
    }
  }, [wsData]);

  // Refresh relative timestamps every 30s
  useEffect(() => {
    const interval = setInterval(() => forceUpdate((n) => n + 1), 30_000);
    return () => clearInterval(interval);
  }, []);

  const dismissAlert = useCallback((id: string) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

  const restoreAll = useCallback(() => {
    setDismissed(new Set());
  }, []);

  const visible = alerts.filter((a) => !dismissed.has(a.id));
  const errorCount   = visible.filter((a) => a.type === 'error').length;
  const warningCount = visible.filter((a) => a.type === 'warning').length;

  return (
    <div
      className="fixed bottom-6 right-6 z-30"
      style={{ width: isExpanded ? '360px' : '320px', transition: 'width 0.3s ease' }}
    >
      <div className="glass-card overflow-hidden" style={{ boxShadow: '0 16px 48px rgba(0,0,0,0.5)' }}>
        {/* Header */}
        <button
          id="alert-feed-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center relative"
              style={{
                background: error
                  ? 'rgba(148,163,184,0.15)'
                  : errorCount > 0
                  ? 'rgba(239,68,68,0.15)'
                  : 'rgba(16,185,129,0.15)',
              }}
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke={error ? '#64748b' : errorCount > 0 ? '#ef4444' : '#10b981'}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {!error && visible.length > 0 && (
                <span
                  className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-xs font-bold flex items-center justify-center"
                  style={{
                    background: errorCount > 0 ? '#ef4444' : '#f59e0b',
                    color: 'white',
                    fontSize: '9px',
                  }}
                >
                  {visible.length}
                </span>
              )}
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Alert Feed</p>
              <p className="text-xs" style={{ color: '#64748b' }}>
                {error ? (
                  'Backend offline'
                ) : loading ? (
                  'Loading alerts...'
                ) : (
                  <>
                    {errorCount > 0 ? `${errorCount} error${errorCount > 1 ? 's' : ''}` : ''}
                    {errorCount > 0 && warningCount > 0 ? ' · ' : ''}
                    {warningCount > 0 ? `${warningCount} warning${warningCount > 1 ? 's' : ''}` : ''}
                    {errorCount === 0 && warningCount === 0 ? 'No critical alerts' : ''}
                  </>
                )}
              </p>
            </div>
          </div>
          <svg
            className="w-4 h-4 transition-transform duration-300"
            style={{
              transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
              color: '#64748b',
            }}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Alert List (collapsible) */}
        <div
          style={{
            maxHeight: isExpanded ? '420px' : '0px',
            overflow: 'hidden',
            transition: 'max-height 0.4s cubic-bezier(0.4,0,0.2,1)',
          }}
        >
          <div
            className="overflow-y-auto"
            style={{
              maxHeight: '400px',
              borderTop: '1px solid rgba(99,102,241,0.1)',
            }}
          >
            {error ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.1)' }}>
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#64748b">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5C3.312 18.333 4.274 20 5.814 20z" />
                  </svg>
                </div>
                <p className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Backend offline</p>
                <p className="text-xs text-center px-4" style={{ color: '#64748b' }}>Backend offline — start docker-compose</p>
              </div>
            ) : loading ? (
              <div className="flex items-center justify-center py-12">
                <svg className="w-6 h-6 animate-spin" fill="none" viewBox="0 0 24 24" style={{ color: '#6366f1' }}>
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            ) : visible.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 gap-3">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="#10b981">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm" style={{ color: '#475569' }}>All clear!</p>
              </div>
            ) : (
              <div className="p-3 space-y-2">
                <style>{`
                  @keyframes flash-highlight {
                    0% { background-color: rgba(99, 102, 241, 0.4); }
                    100% { background-color: rgba(15, 23, 42, 0.5); }
                  }
                `}</style>
                {visible.map((alert) => {
                  const isNew = alert.id === flashEventId;
                  return (
                    <div
                      key={alert.id}
                      className={`alert-item ${alertConfig[alert.type].className}`}
                      style={isNew ? {
                        animation: 'flash-highlight 2s ease-out',
                        border: '1px solid rgba(99, 102, 241, 0.5)',
                        boxShadow: '0 0 12px rgba(99, 102, 241, 0.3)'
                      } : undefined}
                    >
                      {/* Dismiss Button */}
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="absolute top-2.5 right-2.5 w-5 h-5 rounded flex items-center justify-center transition-colors"
                        style={{ color: '#64748b' }}
                        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = '#94a3b8')}
                        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = '#64748b')}
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>

                      <div className="flex items-start gap-2.5 pr-5">
                        <EventIcon type={alert.rawType} className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-0.5">
                            <p className="text-xs font-semibold truncate" style={{ color: '#e2e8f0' }}>
                              {alert.title}
                            </p>
                            <span
                              className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded font-bold"
                              style={{
                                background: `${alertConfig[alert.type].iconColor}20`,
                                color: alertConfig[alert.type].iconColor,
                                fontSize: '9px',
                              }}
                            >
                              {alertConfig[alert.type].label}
                            </span>
                          </div>
                          <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>
                            {alert.message}
                          </p>
                          <div className="flex items-center justify-between mt-1.5">
                            <span className="text-xs" style={{ color: '#334155' }}>
                              {alert.source}
                            </span>
                            <span className="text-xs tabular-nums" style={{ color: '#334155' }}>
                              {formatRelTime(alert.timestamp)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {dismissed.size > 0 && (
              <div className="px-3 pb-3">
                <button
                  onClick={restoreAll}
                  className="w-full py-2 text-xs font-semibold rounded-lg transition-colors"
                  style={{ color: '#6366f1', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)' }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.15)')}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.08)')}
                >
                  Restore {dismissed.size} dismissed
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
