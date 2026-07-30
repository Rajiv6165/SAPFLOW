import type { Metadata } from 'next';
import DashboardClient from '@/components/DashboardClient';

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Real-time SAP S/4HANA transport pipeline monitoring and operations overview.',
};

export default function Page() {
  return <DashboardClient />;
}
