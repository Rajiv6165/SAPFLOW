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
  
  // Phase 3 States
  const [isSyncing, setIsSyncing] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [expandedJobIndex, setExpandedJobIndex] = useState<number | null>(null);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await api.syncPipeline();
      const response = await api.getPipelineStatus();
      if (response && response.last_runs) {
        setHttpData(response.last_runs);
      }
    } catch (e) {
      console.error("Sync failed:", e);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleRunClick = async (run: PipelineData) => {
    setSelectedRun(run);
    setShowPanel(true);
    setJobs([]);
    setLoadingJobs(true);
    setExpandedJobIndex(null);
    try {
      const data = await api.getRunJobs(run.run_id);
      if (data) {
        setJobs(data);
      }
    } catch (e) {
      console.error("Failed to load jobs:", e);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleReRun = async () => {
    if (!selectedRun) return;
    setIsTriggering(true);
    try {
      await api.triggerPipeline(selectedRun.branch);
      alert(`Pipeline re-run triggered for branch ${selectedRun.branch}!`);
      setShowPanel(false);
    } catch (e) {
      console.error(e);
      alert("Failed to trigger re-run");
    } finally {
      setIsTriggering(false);
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-4 h-4 text-rose-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'running':
        return (
          <svg className="w-4 h-4 text-amber-500 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        );
    }
  };

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
          <div className="flex items-center gap-3">
            {/* Sync Now Button */}
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
              style={{
                background: 'rgba(99,102,241,0.12)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
              onMouseEnter={(e) => {
                if (!isSyncing) {
                  (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.2)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.3)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSyncing) {
                  (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.12)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.2)';
                }
              }}
            >
              <svg
                className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
              </svg>
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </button>

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
                onClick={() => handleRunClick(run)}
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
          <div className="modal-panel overflow-y-auto max-h-[90vh]" onClick={(e) => e.stopPropagation()} style={{ width: '450px' }}>
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
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Run ID',       value: selectedRun.run_id, mono: false },
                  { label: 'Branch',       value: selectedRun.branch, mono: false },
                  { label: 'Commit SHA',   value: selectedRun.commit_sha, mono: true },
                  { label: 'Duration',     value: formatDuration(selectedRun.duration_seconds), mono: false },
                ].map(({ label, value, mono }) => (
                  <div key={label} className="glass-card-sm p-3">
                    <p className="text-[11px] mb-1" style={{ color: '#475569' }}>{label}</p>
                    <p className={`text-xs font-semibold ${mono ? 'font-mono' : ''} truncate`} style={{ color: '#e2e8f0' }}>
                      {value}
                    </p>
                  </div>
                ))}
              </div>
              
              <div className="flex items-center justify-between gap-3">
                <div className="glass-card-sm p-3 flex-1">
                  <p className="text-[11px] mb-1" style={{ color: '#475569' }}>Transport ID</p>
                  <p className="text-xs font-semibold" style={{ color: '#e2e8f0' }}>
                    {selectedRun.transport_id ?? 'N/A'}
                  </p>
                </div>
                <div className="glass-card-sm p-3 flex-1">
                  <p className="text-[11px] mb-1.5" style={{ color: '#475569' }}>Status</p>
                  {getStatusBadge(selectedRun.status)}
                </div>
              </div>

              {/* Job Breakdown Section */}
              <div className="mt-4 pt-4 border-t border-slate-800/80">
                <h4 className="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wider">Jobs & Steps</h4>
                {loadingJobs ? (
                  <div className="flex items-center justify-center py-8 gap-2.5">
                    <svg className="w-5 h-5 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    <span className="text-xs text-slate-500 font-medium">Fetching job statuses...</span>
                  </div>
                ) : jobs.length === 0 ? (
                  <div className="py-4 text-center">
                    <p className="text-xs text-slate-500">No job statuses reported for this run.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {jobs.map((job, idx) => {
                      const isExpanded = idx === expandedJobIndex;
                      return (
                        <div key={job.name} className="glass-card-sm p-3 rounded-xl border border-slate-800/50 bg-slate-900/10">
                          <button
                            className="w-full flex items-center justify-between"
                            onClick={() => setExpandedJobIndex(isExpanded ? null : idx)}
                          >
                            <div className="flex items-center gap-2">
                              {getJobStatusIcon(job.status)}
                              <span className="text-xs font-semibold text-slate-300">{job.name}</span>
                            </div>
                            <div className="flex items-center gap-2.5">
                              <span className="text-[11px] text-slate-500 font-mono">
                                {job.duration_seconds ? `${job.duration_seconds}s` : '—'}
                              </span>
                              <svg
                                className={`w-3.5 h-3.5 text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </button>
                          
                          {isExpanded && job.steps && (
                            <div className="mt-3 pl-6 space-y-2 border-l border-slate-800/80">
                              {job.steps.map((step: any, sIdx: number) => (
                                <div key={sIdx} className="flex items-center justify-between text-[11px]">
                                  <span className="text-slate-400">{step.name}</span>
                                  <span
                                    className={`font-mono font-bold text-[10px] px-1.5 py-0.5 rounded`}
                                    style={{
                                      background: step.status === 'success' ? 'rgba(16,185,129,0.1)' : (step.status === 'running' ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)'),
                                      color: step.status === 'success' ? '#10b981' : (step.status === 'running' ? '#f59e0b' : '#ef4444')
                                    }}
                                  >
                                    {step.status.toUpperCase()}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-slate-800/80 mt-4">
                <a
                  href={`https://github.com/Rajiv6165/sapflow/actions/runs/${selectedRun.run_id.replace('run-', '')}`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700/50"
                >
                  View on GitHub
                </a>
                <button
                  onClick={handleReRun}
                  disabled={isTriggering}
                  className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                >
                  {isTriggering ? 'Triggering...' : 'Re-run'}
                </button>
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
}
