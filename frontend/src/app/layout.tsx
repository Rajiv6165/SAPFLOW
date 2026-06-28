'use client';

import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
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
          {/* ─── Top Navigation Bar ───────────────────────────────────── */}
          <header
            className="sticky top-0 z-40 border-b"
            style={{
              background: 'rgba(2,6,23,0.85)',
              borderColor: 'rgba(99,102,241,0.12)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
            }}
          >
            <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center justify-between">
              {/* Brand */}
              <div className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-black text-sm"
                  style={{
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    boxShadow: '0 4px 12px rgba(99,102,241,0.4)',
                  }}
                >
                  SF
                </div>
                <div>
                  <h1 className="text-base font-bold tracking-tight" style={{ color: '#f1f5f9' }}>
                    SAPFlow
                  </h1>
                  <p className="text-xs hidden sm:block" style={{ color: '#64748b' }}>
                    S/4HANA Transport Pipeline
                  </p>
                </div>
              </div>

              {/* Right Side */}
              <div className="flex items-center gap-6">
                {/* AWS Badge */}
                <div className="hidden md:flex items-center gap-2">
                  <span className="text-xs font-medium" style={{ color: '#64748b' }}>
                    Powered by
                  </span>
                  <span
                    className="px-2 py-0.5 rounded text-xs font-bold"
                    style={{ background: 'rgba(245,158,11,0.15)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}
                  >
                    AWS
                  </span>
                  <span
                    className="px-2 py-0.5 rounded text-xs font-bold"
                    style={{ background: 'rgba(0,120,212,0.15)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.2)' }}
                  >
                    SAP BTP
                  </span>
                </div>

                {/* API Docs Link */}
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hidden md:flex items-center gap-1.5 text-xs font-medium transition-colors"
                  style={{ color: '#64748b' }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = '#6366f1')}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = '#64748b')}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  API Docs
                </a>
              </div>
            </div>
          </header>

          {/* ─── Main Content ─────────────────────────────────────────── */}
          <main className="flex-1 max-w-screen-2xl w-full mx-auto px-4 sm:px-6 py-6">
            {children}
          </main>

          {/* ─── Footer ───────────────────────────────────────────────── */}
          <footer
            className="border-t py-4 px-6"
            style={{
              borderColor: 'rgba(99,102,241,0.08)',
              background: 'rgba(2,6,23,0.5)',
            }}
          >
            <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
              <p className="text-xs" style={{ color: '#475569' }}>
                SAPFlow © 2024 — Production CI/CD for SAP S/4HANA
              </p>
              <p className="text-xs" style={{ color: '#475569' }}>
                FastAPI · Next.js · PostgreSQL · Redis · AWS · SAP BTP
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
