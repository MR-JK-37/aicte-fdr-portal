import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { App } from './App';
import { DesignSystemShowcase } from './design-system/DesignSystemShowcase';
import { AuthProvider } from './auth/AuthContext';
import { StepUpProvider } from './auth/StepUpContext';
import './index.css';

// Internal, dev-only route: no router dependency needed for a single
// hidden path. Not linked from any nav; see design-system/README.md.
const isShowcaseRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/_design-system');

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {isShowcaseRoute ? (
      <DesignSystemShowcase />
    ) : (
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <StepUpProvider>
            <App />
          </StepUpProvider>
        </AuthProvider>
      </QueryClientProvider>
    )}
  </React.StrictMode>
);
