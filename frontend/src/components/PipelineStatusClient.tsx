'use client';

import { useEffect } from 'react';
import PipelineStatus from '@/components/PipelineStatus';
import AlertFeed from '@/components/AlertFeed';

export default function PipelineStatusClient() {
  useEffect(() => {
    document.title = 'Pipeline Status | SAPFlow';
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-sans">
          Pipeline Status
        </h2>
        <p className="text-sm mt-0.5 text-slate-400">
          Automated CI/CD transport execution pipeline status and live step logging.
        </p>
      </div>

      <PipelineStatus />
      <AlertFeed />
    </div>
  );
}
