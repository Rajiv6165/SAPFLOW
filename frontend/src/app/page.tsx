'use client';

import { usePipelineWebSocket } from '@/lib/websocket';
import PipelineStatus from '@/components/PipelineStatus';
import TransportTable from '@/components/TransportTable';
import SystemHealth from '@/components/SystemHealth';
import AlertFeed from '@/components/AlertFeed';
import MetricsChart from '@/components/MetricsChart';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface DashboardStats {
  totalRunsToday: number;
  successRate: number;
  activeTransports: number;
  systemStatus: 'healthy' | 'degraded' | 'down' | 'unknown';
}

export default function Home() {
  const { isConnected, lastUpdated } = usePipelineWebSocket();
  const [stats, setStats] = useState<DashboardStats>({
    totalRunsToday: 0,
    successRate: 0,
    activeTransports: 0,
    systemStatus: 'unknown',
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [pipelineData, transportsData, healthData] = await Promise.allSettled([
          api.getPipelineStatus(),
          api.getActiveTransports(),
          api.getSystemHealth(),
        ]);

        const today = new Date().toDateString();
        let runsToday = 0;
        let successCount = 0;

        if (pipelineData.status === 'fulfilled') {
          const todaysRuns = pipelineData.value.last_runs.filter(
            (r) => new Date(r.triggered_at).toDateString() === today
          );
          runsToday = todaysRuns.length;
          successCount = todaysRuns.filter((r) => r.status === 'success').length;
        }

        const activeCount =
          transportsData.status === 'fulfilled'
            ? transportsData.value.transports.length
            : 0;

        const sysStatus =
          healthData.status === 'fulfilled' ? healthData.value.status : 'unknown';

        setStats({
          totalRunsToday: runsToday,
          successRate: runsToday > 0 ? Math.round((successCount / runsToday) * 100) : 0,
          activeTransports: activeCount,
          systemStatus: sysStatus as DashboardStats['systemStatus'],
        });
      } catch {
        // stats remain at defaults
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const systemStatusConfig = {
    healthy: { label: 'All Systems Operational', color: '#10b981', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.25)' },
    degraded: { label: 'Degraded Performance',   color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.25)' },
    down:     { label: 'System Down',             color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.25)'  },
    unknown:  { label: 'Connecting...',           color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.15)'},
  };
  const statusCfg = systemStatusConfig[stats.systemStatus];

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ─── Live Status Banner ──────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2
            className="text-2xl font-bold tracking-tight"
            style={{ color: '#f1f5f9', fontFamily: 'Inter, sans-serif' }}
          >
            Operations Dashboard
          </h2>
          <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>
            Real-time SAP S/4HANA transport pipeline monitoring
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* WS Connection Status */}
          <div
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold"
            style={{
              background: isConnected ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.08)',
              border: `1px solid ${isConnected ? 'rgba(16,185,129,0.25)' : 'rgba(148,163,184,0.15)'}`,
              color: isConnected ? '#34d399' : '#94a3b8',
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{
                background: isConnected ? '#10b981' : '#64748b',
                boxShadow: isConnected ? '0 0 6px #10b981' : 'none',
                animation: isConnected ? 'pulse-glow 2s ease-in-out infinite' : 'none',
              }}
            />
            {isConnected ? 'Live WebSocket' : 'HTTP Fallback'}
          </div>
          {/* Last Updated */}
          {lastUpdated && (
            <span className="text-xs" style={{ color: '#475569' }}>
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* ─── 4-Tile Summary Row ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Runs Today */}
        <div className="stat-tile group">
          <div className="flex items-start justify-between">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.2)' }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: 'rgba(99,102,241,0.1)', color: '#818cf8' }}>
              Today
            </span>
          </div>
          <div className="mt-2">
            <p className="stat-tile-value" style={{ color: '#6366f1' }}>
              {stats.totalRunsToday}
            </p>
            <p className="stat-tile-label">Total Runs Today</p>
          </div>
        </div>

        {/* Success Rate */}
        <div className="stat-tile group">
          <div className="flex items-start justify-between">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.2)' }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#10b981">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{
                background: stats.successRate >= 80 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                color: stats.successRate >= 80 ? '#34d399' : '#f87171',
              }}
            >
              {stats.successRate >= 80 ? '▲ Good' : '▼ Low'}
            </span>
          </div>
          <div className="mt-2">
            <p className="stat-tile-value" style={{ color: stats.successRate >= 80 ? '#10b981' : '#ef4444' }}>
              {stats.successRate}%
            </p>
            <p className="stat-tile-label">Success Rate</p>
          </div>
        </div>

        {/* Active Transports */}
        <div className="stat-tile group">
          <div className="flex items-start justify-between">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)' }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#3b82f6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa' }}>
              Open
            </span>
          </div>
          <div className="mt-2">
            <p className="stat-tile-value" style={{ color: '#3b82f6' }}>
              {stats.activeTransports}
            </p>
            <p className="stat-tile-label">Active Transports</p>
          </div>
        </div>

        {/* System Status */}
        <div className="stat-tile group">
          <div className="flex items-start justify-between">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: statusCfg.bg, border: `1px solid ${statusCfg.border}` }}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke={statusCfg.color}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <span
              className="w-2 h-2 rounded-full mt-1"
              style={{
                background: statusCfg.color,
                boxShadow: `0 0 6px ${statusCfg.color}`,
                animation: stats.systemStatus === 'healthy' ? 'pulse-glow 2s infinite' : 'none',
              }}
            />
          </div>
          <div className="mt-2">
            <p className="stat-tile-value text-xl" style={{ color: statusCfg.color }}>
              {stats.systemStatus === 'unknown' ? '—' : stats.systemStatus.charAt(0).toUpperCase() + stats.systemStatus.slice(1)}
            </p>
            <p className="stat-tile-label">{statusCfg.label}</p>
          </div>
        </div>
      </div>

      {/* ─── 2-Column: Pipeline + System Health ─────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PipelineStatus />
        <SystemHealth />
      </div>

      {/* ─── Full-Width: Metrics Chart ───────────────────────────────── */}
      <MetricsChart />

      {/* ─── Full-Width: Transport Table ─────────────────────────────── */}
      <TransportTable />

      {/* ─── Floating Alert Feed (fixed bottom-right) ────────────────── */}
      <AlertFeed />
    </div>
  );
}
