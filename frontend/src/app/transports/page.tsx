import type { Metadata } from 'next';
import TransportHistoryClient from '@/components/TransportHistoryClient';

export const metadata: Metadata = {
  title: 'Transport History',
  description: 'Track and manage S/4HANA transport requests across landscapes.',
};

export default function Page() {
  return <TransportHistoryClient />;
}
