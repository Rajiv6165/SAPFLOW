import type { Metadata } from 'next';
import './globals.css';
import Providers from './providers';
import Navigation from '@/components/Navigation';

export const metadata: Metadata = {
  title: {
    default: 'Dashboard | SAPFlow',
    template: '%s | SAPFlow',
  },
  description: 'Enterprise SAP S/4HANA Transport Automation & AWS Integration Platform',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icon.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/site.webmanifest',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
      </head>
      <body>
        <Providers>
          {/* Ambient background orbs */}
          <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
            <div
              className="absolute -top-40 -left-40 w-96 h-96 rounded-full opacity-20"
              style={{
                background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)',
                filter: 'blur(60px)',
              }}
            />
            <div
              className="absolute top-1/2 -right-40 w-80 h-80 rounded-full opacity-15"
              style={{
                background: 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)',
                filter: 'blur(60px)',
              }}
            />
            <div
              className="absolute -bottom-40 left-1/3 w-96 h-96 rounded-full opacity-10"
              style={{
                background: 'radial-gradient(circle, #10b981 0%, transparent 70%)',
                filter: 'blur(80px)',
              }}
            />
          </div>

          <div className="min-h-screen flex flex-col">
            <Navigation />

            {/* ─── Main Content ─────────────────────────────────────────── */}
            <main className="flex-1 max-w-screen-2xl w-full mx-auto px-4 sm:px-6 py-6">
              {children}
            </main>

            {/* ─── Footer ───────────────────────────────────────────────── */}
            <footer className="border-t py-4 px-6 border-slate-200/50 dark:border-indigo-500/10">
              <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  SAPFlow © 2024 — Production CI/CD for SAP S/4HANA
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  FastAPI · Next.js · PostgreSQL · Redis · AWS · SAP BTP
                </p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
