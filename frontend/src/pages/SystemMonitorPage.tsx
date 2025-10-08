/**
 * SystemMonitorPage Component
 * Page for system monitoring and performance metrics
 */

import { lazy, Suspense } from 'react';
const SystemMonitor = lazy(() => import('../components/SystemMonitor'));

const SystemMonitorPage: React.FC = () => {
  return (
    <div>
      <Suspense fallback={<div className="h-64 rounded-md bg-gray-100 dark:bg-gray-800 animate-pulse" /> }>
        <SystemMonitor />
      </Suspense>
    </div>
  );
};

export default SystemMonitorPage;
