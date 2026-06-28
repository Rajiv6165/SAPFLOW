'use client';

import { usePipelineWebSocket, PipelineData } from '@/lib/websocket';
import { api } from '@/lib/api';
import { useEffect, useState } from 'react';

interface PipelineStatusProps {
  wsData?: PipelineData[];
}

export default function PipelineStatus({ wsData }: PipelineStatusProps) {
  const { data: wsPipelineData, isConnected } = usePipelineWebSocket();
  const [httpData, setHttpData] = useState<PipelineData[]>([]);
  const [selectedRun, setSelectedRun] = useState<PipelineData | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getPipelineStatus()
      .then((response) => {
        if (response && response.last_runs) {
          setHttpData(response.last_runs);
          setError(false);
        } else {
          setError(true);
        }
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const actualLoading = loading && (!isConnected || !wsPipelineData);
  const actualError = error && !isConnected;

  const displayData = wsData ?? (wsPipelineData?.recent_runs ?? httpData);

  if (actualLoading) {
    return (
      <div className="glass-card p-6 h-full flex flex-col">
        <div className="mb-5">
          <p className="section-title mb-1">CI/CD PIPELINE</p>
          <h3 className="card-title">Pipeline Status</h3>
        </div>
        <div className="space-y-3 flex-1">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/40 border border-slate-800 animate-pulse">
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-800/80 rounded w-1/3" />
                <div className="h-3 bg-slate-800/60 rounded w-1/4" />
              </div>
              <div className="h-6 bg-slate-800 rounded w-16" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (actualError) {
    return (
      <div className="glass-card p-6 h-full flex flex-col">
        <div className="mb-5">
          <p className="section-title mb-1">CI/CD PIPELINE</p>
          <h3 className="card-title">Pipeline Status</h3>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center py-12 gap-3">
          <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.1)' }}>
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#ef4444">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5C3.312 18.333 4.274 20 5.814 20z" />
            </svg>
          </div>
          <p className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Backend offline</p>
          <p className="text-xs text-center" style={{ color: '#64748b' }}>Backend offline — start docker-compose</p>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="badge-success">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            SUCCESS
          </span>
        );
      case 'failed':
        return (
          <span className="badge-failed">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            FAILED
          </span>
        );
      case 'running':
        return (
          <span className="badge-running">
            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            RUNNING
          </span>
        );
      default:
        return (
          <span className="badge-pending">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            PENDING
          </span>
        );
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '—';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const formatRelTime = (dateString: string) => {
    const diff = Date.now() - new Date(dateString).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBarColor = (status: string) => {
    switch (status) {
      case 'success': return '#10b981';
      case 'failed':  return '#ef4444';
      case 'running': return '#f59e0b';
      default:        return '#475569';
    }
  };

  return (
    <>
      <div className="glass-card p-6 h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <p className="section-title mb-1">CI/CD PIPELINE</p>
            <h3 className="card-title">Pipeline Status</h3>
          </div>
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium"
            style={{
              background: isConnected ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.08)',
              color: isConnected ? '#34d399' : '#94a3b8',
              border: `1px solid ${isConnected ? 'rgba(16,185,129,0.2)' : 'rgba(148,163,184,0.12)'}`,
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: isConnected ? '#10b981' : '#64748b',
                boxShadow: isConnected ? '0 0 4px #10b981' : 'none',
                animation: isConnected ? 'pulse-glow 2s infinite' : 'none',
              }}
            />
            {isConnected ? 'Live' : 'HTTP'}
          </div>
        </div>

        {/* Run List */}
        <div className="space-y-2">
          {displayData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <p className="text-sm" style={{ color: '#475569' }}>No pipeline runs yet</p>
            </div>
          ) : (
            displayData.map((run) => (
              <button
                key={run.run_id}
                onClick={() => { setSelectedRun(run); setShowPanel(true); }}
                className="w-full text-left"
              >
                <div
                  className="flex items-center gap-3 p-3 rounded-xl transition-all duration-200 group"
                  style={{
                    background: 'rgba(15,23,42,0.5)',
                    border: '1px solid rgba(148,163,184,0.06)',
                    borderLeft: `3px solid ${getStatusBarColor(run.status)}`,
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.08)';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.2)';
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(15,23,42,0.5)';
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(148,163,184,0.06)';
                  }}
                >
                  {/* Branch + SHA */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                      <p className="text-sm font-semibold truncate" style={{ color: '#e2e8f0' }}>
                        {run.branch}
                      </p>
                    </div>
                    <p className="text-xs mt-0.5 font-mono" style={{ color: '#475569' }}>
                      {run.commit_sha.substring(0, 7)}
                    </p>
                  </div>

                  {/* Duration */}
                  <div className="text-right hidden sm:block">
                    <p className="text-xs font-medium" style={{ color: '#64748b' }}>
                      {formatDuration(run.duration_seconds)}
                    </p>
                    <p className="text-xs" style={{ color: '#334155' }}>
                      {formatRelTime(run.triggered_at)}
                    </p>
                  </div>

                  {/* Badge */}
                  <div className="flex-shrink-0">{getStatusBadge(run.status)}</div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* ─── Detail Side Panel (Modal) ────────────────────────────── */}
      {showPanel && selectedRun && (
        <div className="modal-overlay" onClick={() => setShowPanel(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="section-title mb-1">PIPELINE RUN</p>
                <h3 className="card-title">Run Details</h3>
              </div>
              <button
                onClick={() => setShowPanel(false)}
                className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                style={{ background: 'rgba(148,163,184,0.08)', color: '#64748b' }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,0.1)')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(148,163,184,0.08)')}
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {[
                { label: 'Run ID',       value: selectedRun.run_id, mono: false },
                { label: 'Branch',       value: selectedRun.branch, mono: false },
                { label: 'Commit SHA',   value: selectedRun.commit_sha, mono: true },
                { label: 'Duration',     value: formatDuration(selectedRun.duration_seconds), mono: false },
                { label: 'Transport ID', value: selectedRun.transport_id ?? 'N/A', mono: false },
              ].map(({ label, value, mono }) => (
                <div key={label} className="glass-card-sm p-3">
                  <p className="text-xs mb-1" style={{ color: '#475569' }}>{label}</p>
                  <p className={`text-sm font-semibold ${mono ? 'font-mono' : ''}`} style={{ color: '#e2e8f0' }}>
                    {value}
                  </p>
                </div>
              ))}
              <div className="glass-card-sm p-3">
                <p className="text-xs mb-2" style={{ color: '#475569' }}>Status</p>
                {getStatusBadge(selectedRun.status)}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
