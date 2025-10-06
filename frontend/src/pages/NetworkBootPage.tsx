/**
 * NetworkBootPage Component
 * Page for monitoring network boot processes
 */

import React from 'react';
import NetworkBootMonitor from '../components/NetworkBootMonitor';

const NetworkBootPage: React.FC = () => {
  return (
    <div>
      <NetworkBootMonitor />
    </div>
  );
};

export default NetworkBootPage;
