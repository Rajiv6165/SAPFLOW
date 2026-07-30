'use client';

import { useEffect } from 'react';
import TransportTable from '@/components/TransportTable';
import AlertFeed from '@/components/AlertFeed';

export default function TransportHistoryClient() {
  useEffect(() => {
    document.title = 'Transport History | SAPFlow';
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-sans">
          Transport History
        </h2>
        <p className="text-sm mt-0.5 text-slate-400">
          Track and manage S/4HANA transport requests across landscapes.
        </p>
      </div>

      <TransportTable />
      <AlertFeed />
    </div>
  );
}
