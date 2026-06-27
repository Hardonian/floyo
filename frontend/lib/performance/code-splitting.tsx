/**
 * Code Splitting Utilities
 * 
 * Dynamic imports and route-based code splitting helpers.
 */

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';

/**
 * Create a dynamically imported component with loading state
 */
export function createDynamicComponent<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options?: {
    loading?: () => React.ReactNode;
    ssr?: boolean;
  }
) {
  return dynamic(importFunc, {
    loading: options?.loading,
    ssr: options?.ssr ?? true,
  });
}

/**
 * Lazy load heavy components
 */
export const LazyChart = dynamic(() => import('@/components/ui/chart'), {
  ssr: false,
  loading: () => <div className="h-[300px] flex items-center justify-center">Loading chart...</div>,
});

export const LazyWorkflowBuilder = dynamic(
  () => import('@/components/workflows/WorkflowBuilder'),
  {
    ssr: false,
    loading: () => <div className="h-[400px] flex items-center justify-center">Loading workflow builder...</div>,
  }
);

export const LazyAnalyticsDashboard = dynamic(
  () => import('@/components/analytics/AnalyticsDashboard'),
  {
    ssr: false,
    loading: () => <div className="h-[500px] flex items-center justify-center">Loading analytics...</div>,
  }
);
