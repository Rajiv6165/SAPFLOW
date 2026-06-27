'use client';

import { useState, useEffect } from 'react';
import { api, SystemHealth as SystemHealthType } from '@/lib/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface HealthHistoryItem {
  recorded_at: string;
  cpu_percent: number;
  memory_percent: number;
  active_users: number;
  avg_response_ms: number;
}

interface MetricCardProps {
  label: string;
  value: string;
  unit?: string;
  color: string;
  bg: string;
  border: string;
  icon: React.ReactNode;
  sparkData: { value: number }[];
  lineColor: string;
}

function MetricCard({ label, value, unit, color, bg, border, icon, sparkData, lineColor }: MetricCardProps) {
  return (
    <div
      className="rounded-xl p-4 transition-all duration-300 hover:scale-[1.01]"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span style={{ color }}>{icon}</span>
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#64748b' }}>
            {label}
          </span>
        </div>
        <span className="text-lg font-bold" style={{ color }}>
          {value}
          {unit && <span className="text-xs ml-0.5 font-medium">{unit}</span>}
        </span>
      </div>
      <div className="h-14">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={sparkData}>
            <XAxis dataKey="time" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                background: 'rgba(15,23,42,0.9)',
                border: `1px solid ${border}`,
                borderRadius: '8px',
                fontSize: '11px',
                color: '#e2e8f0',
              }}
              itemStyle={{ color }}
              labelStyle={{ display: 'none' }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={lineColor}
              strokeWidth={2}
              dot={false}
              strokeOpacity={0.9}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function SystemHealth() {
  const [health, setHealth] = useState<SystemHealthType | null>(null);
  const [history, setHistory] = useState<HealthHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [currentHealth, healthHistory] = await Promise.all([
        api.getSystemHealth(),
        api.getHealthHistory(10),
      ]);
      setHealth(currentHealth);
      setHistory(healthHistory);
    } catch {
      // fail silently; show loading state
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getMetricThreshold = (value: number, type: 'cpu' | 'memory' | 'response') => {
    if (type === 'response') {
      if (value > 1000) return { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.15)' };
      if (value > 500)  return { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.15)' };
      return { color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.15)' };
    }
    if (value > 95) return { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.15)' };
    if (value > 80) return { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.15)' };
    return { color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.15)' };
  };

  const sparkline = (metric: keyof HealthHistoryItem) =>
    [...history].reverse().map((h) => ({ value: Number(h[metric]) }));

  const statusConfig = {
    healthy: { label: 'All Systems Nominal', color: '#10b981', dot: '#10b981' },
    degraded: { label: 'Degraded Performance', color: '#f59e0b', dot: '#f59e0b' },
    down:    { label: 'System Offline',       color: '#ef4444', dot: '#ef4444' },
  };
  const scfg = health ? (statusConfig[health.status as keyof typeof statusConfig] ?? statusConfig.healthy) : null;

  if (loading) {
    return (
      <div className="glass-card p-6 h-full flex flex-col">
        <div className="mb-5">
          <p className="section-title mb-1">INFRASTRUCTURE</p>
          <h3 className="card-title">System Health</h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <svg className="w-8 h-8 animate-spin" fill="none" viewBox="0 0 24 24" style={{ color: '#6366f1' }}>
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm" style={{ color: '#475569' }}>Loading health metrics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="glass-card p-6 h-full flex flex-col">
        <div className="mb-5">
          <p className="section-title mb-1">INFRASTRUCTURE</p>
          <h3 className="card-title">System Health</h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.1)' }}>
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#ef4444">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5C3.312 18.333 4.274 20 5.814 20z" />
              </svg>
            </div>
            <p className="text-sm" style={{ color: '#475569' }}>Backend not reachable</p>
          </div>
        </div>
      </div>
    );
  }

  const cpuT  = getMetricThreshold(health.cpu_percent, 'cpu');
  const memT  = getMetricThreshold(health.memory_percent, 'memory');
  const respT = getMetricThreshold(health.avg_response_ms, 'response');

  const cpuIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3H7a2 2 0 00-2 2v2M9 3h6M9 3V1m6 2h2a2 2 0 012 2v2m0 0V3m0 4v6m0 0h2m-2 0v2a2 2 0 01-2 2h-2m0 0H9m4 0V21m-4 0H7a2 2 0 01-2-2v-2m0 0H3m2 0V9m0 0H3" />
    </svg>
  );
  const memIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
    </svg>
  );
  const userIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
  const clockIcon = (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );

  return (
    <div className="glass-card p-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="section-title mb-1">INFRASTRUCTURE</p>
          <h3 className="card-title">System Health</h3>
        </div>
        {scfg && (
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold"
            style={{
              background: `${scfg.color}18`,
              border: `1px solid ${scfg.color}30`,
              color: scfg.color,
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: scfg.dot,
                boxShadow: `0 0 4px ${scfg.dot}`,
                animation: health.status === 'healthy' ? 'pulse-glow 2s infinite' : 'none',
              }}
            />
            {scfg.label}
          </div>
        )}
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="CPU Usage"
          value={health.cpu_percent.toFixed(1)}
          unit="%"
          color={cpuT.color}
          bg={cpuT.bg}
          border={cpuT.border}
          icon={cpuIcon}
          sparkData={sparkline('cpu_percent')}
          lineColor={cpuT.color}
        />
        <MetricCard
          label="Memory"
          value={health.memory_percent.toFixed(1)}
          unit="%"
          color={memT.color}
          bg={memT.bg}
          border={memT.border}
          icon={memIcon}
          sparkData={sparkline('memory_percent')}
          lineColor={memT.color}
        />
        <MetricCard
          label="Active Users"
          value={String(health.active_users)}
          color="#3b82f6"
          bg="rgba(59,130,246,0.08)"
          border="rgba(59,130,246,0.15)"
          icon={userIcon}
          sparkData={sparkline('active_users')}
          lineColor="#3b82f6"
        />
        <MetricCard
          label="Avg Response"
          value={String(health.avg_response_ms)}
          unit="ms"
          color={respT.color}
          bg={respT.bg}
          border={respT.border}
          icon={clockIcon}
          sparkData={sparkline('avg_response_ms')}
          lineColor={respT.color}
        />
      </div>
    </div>
  );
}
