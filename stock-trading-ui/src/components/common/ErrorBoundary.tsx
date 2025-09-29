'use client';

import React, { ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  title?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="card-professional">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-400">
              <AlertTriangle className="h-4 w-4" />
              {this.props.title || 'Component Error'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <p className="text-gray-400 mb-4">
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => this.setState({ hasError: false, error: undefined })}
                className="text-gray-300 border-gray-600 hover:bg-gray-700"
              >
                <RefreshCw className="h-3 w-3 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Functional component wrapper for easier use
export function TradingErrorBoundary({ children, title }: { children: ReactNode; title?: string }) {
  return (
    <ErrorBoundary
      title={title}
      fallback={
        <div className="p-4 border border-yellow-500/20 bg-yellow-500/10 rounded-lg">
          <div className="flex items-center gap-2 text-yellow-400 mb-2">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">{title || 'Component Error'}</span>
          </div>
          <p className="text-xs text-gray-400">
            Component failed to load. Using demo mode.
          </p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}