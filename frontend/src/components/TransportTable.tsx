'use client';

import { useState, useEffect } from 'react';
import { api, TransportRecord } from '@/lib/api';

type NotificationType = { type: 'success' | 'error'; message: string };

export default function TransportTable() {
  const [transports, setTransports] = useState<TransportRecord[]>([]);
  const [filtered, setFiltered] = useState<TransportRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [landscapeFilter, setLandscapeFilter] = useState('all');
  const [landscapes, setLandscapes] = useState<string[]>(['DEFAULT', 'FINANCE', 'LOGISTICS']);
  const [showModal, setShowModal] = useState(false);
  const [showRollbackModal, setShowRollbackModal] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<TransportRecord | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    transport_id: '',
    source_system: 'DEV',
    target_system: 'QA',
    promoted_by: '',
    landscape: 'DEFAULT',
  });
  const [notification, setNotification] = useState<NotificationType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const loadTransports = async (targetPage: number = page) => {
    setLoading(true);
    try {
      const response = await api.getTransportHistory(landscapeFilter, targetPage, limit);
      if (response && response.items) {
        setTransports(response.items);
        setTotalPages(response.total_pages || 1);
        setTotalItems(response.total || 0);
        setError(false);
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const loadLandscapes = async () => {
    try {
      const response = await api.getLandscapes();
      if (response) {
        setLandscapes(response);
      }
    } catch {
      // fallback to default list
    }
  };

  useEffect(() => {
    loadLandscapes();
  }, []);

  useEffect(() => {
    loadTransports(page);
  }, [page, landscapeFilter]);


  useEffect(() => {
    let result = transports;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      result = result.filter(
        (t) =>
          t.transport_id.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q)
      );
    }
    if (statusFilter !== 'all') {
      result = result.filter((t) => t.status === statusFilter);
    }
    if (landscapeFilter !== 'all') {
      result = result.filter((t) => (t.landscape || 'DEFAULT') === landscapeFilter);
    }
    setFiltered(result);
  }, [searchTerm, statusFilter, landscapeFilter, transports]);

  if (loading) {
    return (
      <div className="glass-card p-6">
        {/* Header Skeleton */}
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p className="section-title mb-1">TRANSPORT MANAGER</p>
            <h3 className="card-title">Transport History</h3>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-9 w-28 bg-slate-800/80 rounded-xl animate-pulse" />
            <div className="h-9 w-36 bg-slate-800/80 rounded-xl animate-pulse" />
          </div>
        </div>

        {/* Filters Skeleton */}
        <div className="flex items-center gap-3 mb-5 flex-wrap">
          <div className="h-10 flex-1 min-w-48 bg-slate-900/60 border border-slate-800/80 rounded-xl animate-pulse" />
          <div className="h-10 w-36 bg-slate-900/60 border border-slate-800/80 rounded-xl animate-pulse" />
          <div className="h-10 w-32 bg-slate-900/60 border border-slate-800/80 rounded-xl animate-pulse" />
        </div>

        {/* Table Rows Skeleton */}
        <div className="overflow-x-auto rounded-xl border border-slate-800/80">
          <div className="p-4 bg-slate-900/40 border-b border-slate-800/80 flex items-center justify-between">
            <div className="h-4 w-24 bg-slate-800/80 rounded animate-pulse" />
            <div className="h-4 w-32 bg-slate-800/80 rounded animate-pulse" />
            <div className="h-4 w-28 bg-slate-800/80 rounded animate-pulse" />
            <div className="h-4 w-20 bg-slate-800/80 rounded animate-pulse" />
            <div className="h-4 w-24 bg-slate-800/80 rounded animate-pulse" />
          </div>
          <div className="divide-y divide-slate-800/60">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="p-4 flex items-center justify-between gap-4 animate-pulse bg-slate-900/20">
                <div className="h-4 w-20 bg-slate-800/80 rounded font-mono" />
                <div className="flex-1 space-y-1.5 max-w-xs">
                  <div className="h-4 w-3/4 bg-slate-800/80 rounded" />
                  <div className="h-3 w-1/2 bg-slate-800/50 rounded" />
                </div>
                <div className="h-5 w-24 bg-slate-800/80 rounded-md" />
                <div className="h-5 w-16 bg-slate-800/80 rounded-full" />
                <div className="h-4 w-20 bg-slate-800/60 rounded" />
                <div className="h-4 w-24 bg-slate-800/60 rounded" />
              </div>
            ))}
          </div>
        </div>

        {/* Pagination Skeleton */}
        <div className="flex items-center justify-between mt-4 flex-wrap gap-3 pt-3 border-t border-slate-800/80">
          <div className="h-4 w-48 bg-slate-800/60 rounded animate-pulse" />
          <div className="flex items-center gap-2">
            <div className="h-7 w-20 bg-slate-800/80 rounded-lg animate-pulse" />
            <div className="h-4 w-10 bg-slate-800/60 rounded animate-pulse" />
            <div className="h-7 w-16 bg-slate-800/80 rounded-lg animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p className="section-title mb-1">TRANSPORT MANAGER</p>
            <h3 className="card-title">Transport History</h3>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-12 gap-3">
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

  const showToast = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  const handlePromote = async () => {
    if (!formData.transport_id.trim()) return;
    setIsSubmitting(true);
    try {
      await api.promoteTransport(
        formData.transport_id,
        formData.source_system,
        formData.target_system,
        formData.promoted_by || 'manual',
        formData.landscape || 'DEFAULT'
      );
      showToast('success', `Transport ${formData.transport_id} promoted to ${formData.target_system}`);
      setShowModal(false);
      setFormData({ transport_id: '', source_system: 'DEV', target_system: 'QA', promoted_by: '', landscape: 'DEFAULT' });
      await loadTransports();
    } catch {
      showToast('error', 'Failed to promote transport. Check backend logs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRollbackClick = (t: TransportRecord) => {
    setRollbackTarget(t);
    setShowRollbackModal(true);
  };

  const handleConfirmRollback = async () => {
    if (!rollbackTarget) return;
    const tid = rollbackTarget.transport_id;
    setShowRollbackModal(false);
    
    // Optimistically update status
    setTransports((prev) =>
      prev.map((item) =>
        item.transport_id === tid ? { ...item, status: 'rolling_back' as any } : item
      )
    );
    
    try {
      await api.rollbackTransport(tid);
      showToast('success', `Rollback initiated for ${tid}`);
      await loadTransports();
    } catch {
      showToast('error', `Failed to initiate rollback for ${tid}`);
      await loadTransports();
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':      return <span className="badge-success">Success</span>;
      case 'failed':       return <span className="badge-failed">Failed</span>;
      case 'in_progress':  return <span className="badge-in-progress">In Progress</span>;
      case 'rolling_back': return (
        <span className="px-2 py-0.5 rounded text-xs font-semibold" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
          Rolling Back
        </span>
      );
      default:             return <span className="badge-pending">Pending</span>;
    }
  };

  const getLandscapeBadge = (landscape: string) => {
    switch (landscape) {
      case 'FINANCE':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider" style={{ background: 'rgba(59,130,246,0.12)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)' }}>
            FINANCE
          </span>
        );
      case 'LOGISTICS':
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider" style={{ background: 'rgba(16,185,129,0.12)', color: '#34d399', border: '1px solid rgba(16,185,129,0.2)' }}>
            LOGISTICS
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider" style={{ background: 'rgba(148,163,184,0.12)', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.2)' }}>
            DEFAULT
          </span>
        );
    }
  };

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const escapeCsv = (str: string | undefined | null) => {
    if (str == null) return '""';
    const s = String(str);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const handleExportCsv = () => {
    const rowsToExport = filtered;
    if (!rowsToExport || rowsToExport.length === 0) {
      showToast('error', 'No transport rows to export.');
      return;
    }

    const headers = ['id', 'landscape', 'status', 'promoted_by', 'timestamp'];
    const csvRows = [
      headers.join(','),
      ...rowsToExport.map((t) =>
        [
          escapeCsv(t.transport_id || t.id),
          escapeCsv(t.landscape || 'DEFAULT'),
          escapeCsv(t.status),
          escapeCsv(t.promoted_by),
          escapeCsv(t.promoted_at),
        ].join(',')
      ),
    ];

    const csvString = csvRows.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const dateStr = new Date().toISOString().split('T')[0];
    const filename = `transport-history-${dateStr}.csv`;

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="glass-card p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p className="section-title mb-1">TRANSPORT MANAGER</p>
            <h3 className="card-title">Transport History</h3>
          </div>
          <div className="flex items-center gap-3">
            <button
              id="export-csv-btn"
              onClick={handleExportCsv}
              disabled={filtered.length === 0}
              className="px-3 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: 'rgba(99,102,241,0.12)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)',
              }}
              onMouseEnter={(e) => {
                if (filtered.length > 0) {
                  (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.2)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.3)';
                }
              }}
              onMouseLeave={(e) => {
                if (filtered.length > 0) {
                  (e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.12)';
                  (e.currentTarget as HTMLElement).style.borderColor = 'rgba(99,102,241,0.2)';
                }
              }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export CSV
            </button>
            <button
              id="promote-transport-btn"
              onClick={() => setShowModal(true)}
              className="btn-primary"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Promote Transport
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-5 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
              fill="none" viewBox="0 0 24 24" stroke="#6366f1"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              id="transport-search"
              type="text"
              placeholder="Search transport ID or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-dark pl-10"
            />
          </div>
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="#6366f1"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <select
              id="transport-landscape-filter"
              value={landscapeFilter}
              onChange={(e) => {
                setLandscapeFilter(e.target.value);
                setPage(1);
              }}
              className="select-dark pl-9"
            >
              <option value="all">All Landscapes</option>
              {landscapes.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="#6366f1"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <select
              id="transport-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="select-dark pl-9"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid rgba(99,102,241,0.1)' }}>
          <table className="w-full data-table">
            <thead>
              <tr>
                <th>Transport ID</th>
                <th>Description</th>
                <th>Route</th>
                <th>Status</th>
                <th>Promoted By</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center"
                        style={{ background: 'rgba(99,102,241,0.1)' }}
                      >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <span style={{ color: '#475569', fontSize: '0.875rem' }}>No transports found</span>
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map((t) => (
                  <tr key={t.id}>
                    <td>
                      <span className="font-mono text-xs font-semibold" style={{ color: '#818cf8' }}>
                        {t.transport_id}
                      </span>
                    </td>
                    <td className="max-w-xs">
                      <div className="flex items-center gap-2">
                        {getLandscapeBadge(t.landscape || 'DEFAULT')}
                        <span className="truncate block">{t.description}</span>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-semibold"
                          style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8' }}
                        >
                          {t.source_system}
                        </span>
                        <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="#475569">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                        <span
                          className="px-2 py-0.5 rounded text-xs font-semibold"
                          style={{ background: 'rgba(16,185,129,0.1)', color: '#34d399' }}
                        >
                          {t.target_system}
                        </span>
                      </div>
                    </td>
                    <td>{getStatusBadge(t.status)}</td>
                    <td>
                      <span className="text-xs font-medium" style={{ color: '#94a3b8' }}>
                        {t.promoted_by}
                      </span>
                    </td>
                    <td>
                      <span className="text-xs tabular-nums" style={{ color: '#64748b' }}>
                        {formatDate(t.promoted_at)}
                      </span>
                    </td>
                    <td>
                      {t.status === 'success' && (
                        <button
                          onClick={() => handleRollbackClick(t)}
                          className="px-2 py-1 rounded text-xs font-bold transition-all flex items-center gap-1 cursor-pointer"
                          style={{
                            border: '1px solid rgba(239,68,68,0.4)',
                            color: '#f87171',
                            background: 'transparent',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(239,68,68,0.1)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                          }}
                        >
                          <span>↩</span> Rollback
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination & Row count */}
        <div className="flex items-center justify-between mt-4 flex-wrap gap-3 pt-3" style={{ borderTop: '1px solid rgba(99,102,241,0.1)' }}>
          <p className="text-xs font-medium" style={{ color: '#64748b' }}>
            Showing Page {page} of {totalPages || 1} ({totalItems} total transports)
          </p>
          <div className="flex items-center gap-2">
            <button
              id="transport-prev-page"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1 || loading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                background: 'rgba(99,102,241,0.1)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)'
              }}
            >
              Previous
            </button>
            <span className="text-xs font-mono font-semibold px-2" style={{ color: '#94a3b8' }}>
              {page} / {totalPages || 1}
            </span>
            <button
              id="transport-next-page"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages || totalPages === 0 || loading}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                background: 'rgba(99,102,241,0.1)',
                color: '#818cf8',
                border: '1px solid rgba(99,102,241,0.2)'
              }}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* ─── Promote Modal ──────────────────────────────────────────── */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="section-title mb-1">SAP BTP</p>
                <h3 className="card-title">Promote Transport</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                style={{ background: 'rgba(148,163,184,0.08)', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                  Transport ID *
                </label>
                <input
                  id="modal-transport-id"
                  type="text"
                  value={formData.transport_id}
                  onChange={(e) => setFormData({ ...formData, transport_id: e.target.value })}
                  placeholder="DEVK900001"
                  className="input-dark font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                    From
                  </label>
                  <select
                    id="modal-source-system"
                    value={formData.source_system}
                    onChange={(e) => setFormData({ ...formData, source_system: e.target.value })}
                    className="select-dark"
                  >
                    <option value="DEV">DEV</option>
                    <option value="QA">QA</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                    To
                  </label>
                  <select
                    id="modal-target-system"
                    value={formData.target_system}
                    onChange={(e) => setFormData({ ...formData, target_system: e.target.value })}
                    className="select-dark"
                  >
                    <option value="QA">QA</option>
                    <option value="PROD">PROD</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                    Landscape
                  </label>
                  <select
                    id="modal-landscape"
                    value={formData.landscape}
                    onChange={(e) => setFormData({ ...formData, landscape: e.target.value })}
                    className="select-dark"
                  >
                    {landscapes.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                    Promoted By
                  </label>
                  <input
                    id="modal-promoted-by"
                    type="text"
                    value={formData.promoted_by}
                    onChange={(e) => setFormData({ ...formData, promoted_by: e.target.value })}
                    placeholder="Your name"
                    className="input-dark"
                  />
                </div>
              </div>

              {/* Route Preview */}
              <div
                className="flex items-center justify-center gap-3 py-3 rounded-xl"
                style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' }}
              >
                <span className="px-3 py-1 rounded-lg text-sm font-bold" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>
                  {formData.source_system}
                </span>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <span className="px-3 py-1 rounded-lg text-sm font-bold" style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399' }}>
                  {formData.target_system}
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowModal(false)} className="btn-ghost">
                Cancel
              </button>
              <button
                id="modal-confirm-promote"
                onClick={handlePromote}
                disabled={isSubmitting || !formData.transport_id.trim()}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isSubmitting ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Promoting...
                  </>
                ) : (
                  'Confirm Promote'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Rollback Confirmation Modal ───────────────────────────────── */}
      {showRollbackModal && rollbackTarget && (
        <div className="modal-overlay" onClick={() => setShowRollbackModal(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <div>
                <p className="section-title mb-1" style={{ color: '#ef4444' }}>ROLLBACK TRANSPORT</p>
                <h3 className="card-title">Confirm Rollback</h3>
              </div>
              <button
                onClick={() => setShowRollbackModal(false)}
                className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
                style={{ background: 'rgba(148,163,184,0.08)', color: '#64748b' }}
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <p className="text-sm" style={{ color: '#e2e8f0', lineHeight: 1.6 }}>
                Are you sure you want to rollback <span className="font-mono text-indigo-400 font-bold">{rollbackTarget.transport_id}</span> from <span className="font-bold text-emerald-400">{rollbackTarget.target_system}</span> to <span className="font-bold text-indigo-400">{rollbackTarget.source_system}</span>? This cannot be undone.
              </p>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setShowRollbackModal(false)} className="btn-ghost">
                Cancel
              </button>
              <button
                onClick={handleConfirmRollback}
                className="px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer"
                style={{
                  background: '#ef4444',
                  color: '#fff',
                  boxShadow: '0 0 12px rgba(239,68,68,0.2)'
                }}
              >
                Confirm Rollback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ─── Toast Notification ─────────────────────────────────────── */}
      {notification && (
        <div className={notification.type === 'success' ? 'toast-success' : 'toast-error'}>
          {notification.type === 'success' ? (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          )}
          {notification.message}
        </div>
      )}
    </>
  );
}
