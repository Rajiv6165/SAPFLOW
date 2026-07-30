'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ThemeToggle from '@/components/ThemeToggle';

export default function Navigation() {
  const pathname = usePathname();

  const navItems = [
    { name: 'Dashboard', href: '/' },
    { name: 'Transport History', href: '/transports' },
    { name: 'Pipeline Status', href: '/pipeline' },
    { name: 'System Health', href: '/health' },
    { name: 'Metrics & Analytics', href: '/metrics' },
  ];

  return (
    <header className="sticky top-0 z-40 border-b glass-card !rounded-none border-x-0 border-t-0 bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-screen-2xl mx-auto px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Desktop Nav */}
        <div className="flex items-center gap-6 w-full md:w-auto justify-between md:justify-start">
          <Link href="/" className="flex items-center gap-3 group">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white font-black text-sm transition-transform group-hover:scale-105"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                boxShadow: '0 4px 14px rgba(99,102,241,0.4)',
              }}
            >
              SF
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-slate-100 group-hover:text-indigo-400 transition-colors">
                SAPFlow
              </h1>
              <p className="text-xs hidden sm:block text-slate-400">
                S/4HANA Transport Pipeline
              </p>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1 bg-slate-800/50 p-1 rounded-xl border border-slate-700/50">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Mobile Navigation bar */}
        <nav className="flex lg:hidden items-center gap-1 overflow-x-auto w-full pb-2 border-t border-slate-800/80 pt-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`whitespace-nowrap px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Right Side */}
        <div className="flex items-center gap-4 sm:gap-6 self-end md:self-auto">
          {/* AWS Badge */}
          <div className="hidden md:flex items-center gap-2">
            <span className="text-xs font-medium text-slate-400">
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
            className="hidden md:flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            API Docs
          </a>

          {/* Theme Toggle Button */}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
