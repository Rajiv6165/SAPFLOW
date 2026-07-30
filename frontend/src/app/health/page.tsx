import type { Metadata } from 'next';
import SystemHealthClient from '@/components/SystemHealthClient';

export const metadata: Metadata = {
  title: 'System Health',
  description: 'SAP BTP, AWS CloudWatch, and infrastructure integration health monitoring.',
};

export default function Page() {
  return <SystemHealthClient />;
}
