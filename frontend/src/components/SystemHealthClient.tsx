'use client';

import { useEffect } from 'react';
import SystemHealth from '@/components/SystemHealth';
import AlertFeed from '@/components/AlertFeed';

export default function SystemHealthClient() {
  useEffect(() => {
    document.title = 'System Health | SAPFlow';
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-sans">
          System Health
        </h2>
        <p className="text-sm mt-0.5 text-slate-400">
          SAP BTP, AWS CloudWatch, and infrastructure integration health monitoring.
        </p>
      </div>

      <SystemHealth />
      <AlertFeed />
    </div>
  );
}
