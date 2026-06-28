'use client';

import { useState, useEffect } from 'react';
import { api, TransportRecord } from '@/lib/api';

type NotificationType = { type: 'success' | 'error'; message: string };

export default function TransportTable() {
  const [transports, setTransports] = useState<TransportRecord[]>([]);
  const [filtered, setFiltered] = useState<TransportRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    transport_id: '',
    source_system: 'DEV',
    target_system: 'QA',
    promoted_by: '',
  });
  const [notification, setNotification] = useState<NotificationType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadTransports = async () => {
    setLoading(true);
    try {
      const response = await api.getTransportHistory();
      if (response && response.transports) {
        setTransports(response.transports);
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

  useEffect(() => { loadTransports(); }, []);

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
    setFiltered(result);
  }, [searchTerm, statusFilter, transports]);

  if (loading) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p className="section-title mb-1">TRANSPORT MANAGER</p>
            <h3 className="card-title">Transport History</h3>
          </div>
        </div>
        <div className="space-y-4">
          <div className="h-10 bg-slate-800/40 rounded-xl animate-pulse w-full" />
          <div className="h-32 bg-slate-800/20 rounded-xl animate-pulse w-full" />
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
        formData.promoted_by || 'manual'
      );
      showToast('success', `Transport ${formData.transport_id} promoted to ${formData.target_system}`);
      setShowModal(false);
      setFormData({ transport_id: '', source_system: 'DEV', target_system: 'QA', promoted_by: '' });
      await loadTransports();
    } catch {
      showToast('error', 'Failed to promote transport. Check backend logs.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':     return <span className="badge-success">Success</span>;
      case 'failed':      return <span className="badge-failed">Failed</span>;
      case 'in_progress': return <span className="badge-in-progress">In Progress</span>;
      default:            return <span className="badge-pending">Pending</span>;
    }
  };

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
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
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
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
                      <span className="truncate block">{t.description}</span>
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
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Row count */}
        {filtered.length > 0 && (
          <p className="text-xs mt-3" style={{ color: '#334155' }}>
            Showing {filtered.length} of {transports.length} transports
          </p>
        )}
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
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wide" style={{ color: '#64748b' }}>
                  Promoted By
                </label>
                <input
                  id="modal-promoted-by"
                  type="text"
                  value={formData.promoted_by}
                  onChange={(e) => setFormData({ ...formData, promoted_by: e.target.value })}
                  placeholder="Your name or team"
                  className="input-dark"
                />
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
