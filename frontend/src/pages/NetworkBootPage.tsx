/**
 * NetworkBootPage Component
 * Page for monitoring network boot processes
 */

// React is available globally;
import NetworkBootMonitor from '../components/NetworkBootMonitor';

const NetworkBootPage: React.FC = () => {
  return (
    <div>
      <NetworkBootMonitor />
    </div>
  );
};

export default NetworkBootPage;
