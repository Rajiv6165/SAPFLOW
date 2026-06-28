'use client';

import { useState, useEffect } from 'react';
import { api, PipelineMetrics } from '@/lib/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  TooltipProps,
} from 'recharts';
import { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';

interface ChartPoint {
  date: string;
  success: number;
  failed: number;
  total: number;
  passRate: string;
}

const CustomTooltip = ({ active, payload, label }: TooltipProps<ValueType, NameType>) => {
  if (active && payload && payload.length) {
    const success = Number(payload[0]?.value ?? 0);
    const failed  = Number(payload[1]?.value ?? 0);
    const total   = success + failed;
    const rate    = total > 0 ? ((success / total) * 100).toFixed(1) : '0';
    return (
      <div
        className="px-4 py-3 rounded-xl text-xs"
        style={{
          background: 'rgba(15,23,42,0.95)',
          border: '1px solid rgba(99,102,241,0.25)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          backdropFilter: 'blur(20px)',
          color: '#e2e8f0',
        }}
      >
        <p className="font-semibold mb-2" style={{ color: '#94a3b8' }}>{label}</p>
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm" style={{ background: '#10b981' }} />
              <span>Success</span>
            </div>
            <span className="font-bold" style={{ color: '#34d399' }}>{success}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm" style={{ background: '#ef4444' }} />
              <span>Failed</span>
            </div>
            <span className="font-bold" style={{ color: '#f87171' }}>{failed}</span>
          </div>
          <div className="flex items-center justify-between gap-4 pt-1 border-t" style={{ borderColor: 'rgba(99,102,241,0.15)' }}>
            <span style={{ color: '#6366f1' }}>Pass Rate</span>
            <span className="font-bold" style={{ color: '#818cf8' }}>{rate}%</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function MetricsChart() {
  const [metrics, setMetrics] = useState<PipelineMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .getPipelineMetrics()
      .then((data) => {
        if (data) {
          setMetrics(data);
          setError(false);
        } else {
          setError(true);
        }
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (error) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <div>
            <p className="section-title mb-1">ANALYTICS</p>
            <h3 className="card-title">Pipeline Metrics — Last 30 Days</h3>
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

  const chartData: ChartPoint[] = metrics.map((m) => ({
    date: new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    success: m.success,
    failed: m.failed,
    total: m.success + m.failed,
    passRate: ((m.success / Math.max(m.success + m.failed, 1)) * 100).toFixed(1),
  }));

  const totalRuns    = chartData.reduce((s, d) => s + d.total, 0);
  const totalSuccess = chartData.reduce((s, d) => s + d.success, 0);
  const totalFailed  = chartData.reduce((s, d) => s + d.failed, 0);
  const overallRate  = totalRuns > 0 ? ((totalSuccess / totalRuns) * 100).toFixed(1) : '0';

  return (
    <div className="glass-card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <p className="section-title mb-1">ANALYTICS</p>
          <h3 className="card-title">Pipeline Metrics — Last 30 Days</h3>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ background: '#10b981' }} />
            <span className="text-xs font-medium" style={{ color: '#64748b' }}>Success</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ background: '#ef4444' }} />
            <span className="text-xs font-medium" style={{ color: '#64748b' }}>Failed</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-64 mb-6">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" style={{ color: '#6366f1' }}>
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span className="text-sm" style={{ color: '#475569' }}>Loading metrics...</span>
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.1)' }}>
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#6366f1">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-sm" style={{ color: '#475569' }}>No metrics data yet</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} barCategoryGap="30%">
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="rgba(99,102,241,0.08)"
              />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#475569', fontFamily: 'Inter' }}
                axisLine={{ stroke: 'rgba(99,102,241,0.1)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#475569', fontFamily: 'Inter' }}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)', radius: 6 }} />
              <Bar dataKey="success" fill="#10b981" radius={[3, 3, 0, 0]} stackId="a" />
              <Bar dataKey="failed"  fill="#ef4444" radius={[3, 3, 0, 0]} stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            label: 'Total Runs',
            value: totalRuns,
            color: '#6366f1',
            bg: 'rgba(99,102,241,0.08)',
            border: 'rgba(99,102,241,0.15)',
          },
          {
            label: 'Overall Pass Rate',
            value: `${overallRate}%`,
            color: totalRuns > 0 && Number(overallRate) >= 80 ? '#10b981' : '#f59e0b',
            bg: totalRuns > 0 && Number(overallRate) >= 80 ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
            border: totalRuns > 0 && Number(overallRate) >= 80 ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
          },
          {
            label: 'Failed Runs',
            value: totalFailed,
            color: totalFailed === 0 ? '#10b981' : '#ef4444',
            bg: totalFailed === 0 ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
            border: totalFailed === 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
          },
        ].map(({ label, value, color, bg, border }) => (
          <div
            key={label}
            className="rounded-xl p-4 text-center"
            style={{ background: bg, border: `1px solid ${border}` }}
          >
            <p className="text-xs font-semibold mb-1 uppercase tracking-wide" style={{ color: '#64748b' }}>
              {label}
            </p>
            <p className="text-2xl font-bold" style={{ color }}>
              {value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
