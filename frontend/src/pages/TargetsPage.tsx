/**
 * TargetsPage Component
 * Page for managing iSCSI targets
 */

import React from 'react';
import TargetManager from '../components/TargetManager';

const TargetsPage: React.FC = () => {
  return (
    <div>
      <TargetManager />
    </div>
  );
};

export default TargetsPage;