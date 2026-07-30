import type { Metadata } from 'next';
import PipelineStatusClient from '@/components/PipelineStatusClient';

export const metadata: Metadata = {
  title: 'Pipeline Status',
  description: 'Automated CI/CD transport execution pipeline status and live step logging.',
};

export default function Page() {
  return <PipelineStatusClient />;
}
