import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('VisualIQ Component Error caught by ErrorBoundary:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          className="card"
          style={{
            margin: '2rem auto',
            maxWidth: '600px',
            padding: '2rem',
            textAlign: 'center',
            border: '1px solid #ef4444',
            background: 'rgba(239, 68, 68, 0.08)',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem',
            }}
          >
            <AlertOctagon size={24} color="#ef4444" />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f87171', marginBottom: '0.5rem' }}>
            {this.props.fallbackTitle || 'Component Encountered an Error'}
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred. The surveillance session remains protected.'}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <button className="btn btn-secondary" onClick={this.handleReset}>
              <RotateCcw size={14} />
              <span>Retry Component</span>
            </button>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>
              <span>Reload Page</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
