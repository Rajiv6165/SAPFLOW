'use client';

import { useEffect } from 'react';
import MetricsChart from '@/components/MetricsChart';
import AlertFeed from '@/components/AlertFeed';

export default function MetricsClient() {
  useEffect(() => {
    document.title = 'Metrics & Analytics | SAPFlow';
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-sans">
          Metrics & Analytics
        </h2>
        <p className="text-sm mt-0.5 text-slate-400">
          Performance metrics, transport velocity, and error rate analytics.
        </p>
      </div>

      <MetricsChart />
      <AlertFeed />
    </div>
  );
}
