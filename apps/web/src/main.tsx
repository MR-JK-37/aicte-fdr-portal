import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { DesignSystemShowcase } from './design-system/DesignSystemShowcase';
import './index.css';

// Internal, dev-only route: no router dependency needed for a single
// hidden path. Not linked from any nav; see design-system/README.md.
const isShowcaseRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/_design-system');

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {isShowcaseRoute ? <DesignSystemShowcase /> : <App />}
  </React.StrictMode>
);
