/**
 * SystemMonitorPage Component
 * Page for system monitoring and performance metrics
 */

import { Suspense, lazy } from 'react';
const SystemMonitor = lazy(() => import('../components/SystemMonitor'));

const SystemMonitorPage: React.FC = () => {
  return (
    <Suspense fallback={<div className="h-[200px] bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" />}> 
      <div>
        <SystemMonitor />
      </div>
    </Suspense>
  );
};

export default SystemMonitorPage;
