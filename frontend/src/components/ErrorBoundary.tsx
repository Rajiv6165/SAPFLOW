'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-slate-950 text-slate-100">
          <div className="glass-card max-w-md w-full p-8 text-center space-y-5 border border-rose-500/20 shadow-2xl">
            <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto text-rose-500">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5C3.312 18.333 4.274 20 5.814 20z" />
              </svg>
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-100 tracking-tight">Something went wrong</h2>
              <p className="text-sm text-slate-400">
                An unexpected error occurred while rendering the application. Reload the page to continue.
              </p>
            </div>

            {this.state.error?.message && (
              <div className="p-3 rounded-xl bg-slate-900/80 border border-rose-900/30 text-rose-400 text-xs font-mono text-left overflow-x-auto max-h-24">
                {this.state.error.message}
              </div>
            )}

            <div className="pt-2">
              <button
                id="error-boundary-reload-btn"
                onClick={this.handleReload}
                className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition-all shadow-lg shadow-rose-600/20 cursor-pointer flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
                </svg>
                Reload the page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
