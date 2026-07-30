import type { Metadata } from 'next';
import MetricsClient from '@/components/MetricsClient';

export const metadata: Metadata = {
  title: 'Metrics & Analytics',
  description: 'Performance metrics, transport velocity, and error rate analytics.',
};

export default function Page() {
  return <MetricsClient />;
}
