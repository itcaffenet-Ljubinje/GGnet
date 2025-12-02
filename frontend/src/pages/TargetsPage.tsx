/**
 * TargetsPage Component
 * Page for managing iSCSI targets
 */

// React is available globally;
import TargetManager from '../components/TargetManager';

const TargetsPage: React.FC = () => {
  return (
    <div>
      <TargetManager />
    </div>
  );
};

export default TargetsPage;