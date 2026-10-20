import { useAuth } from '../../auth.jsx';
import { getToken } from '../../api.js';
import EpaRoutes from './EpaRoutes.jsx';
import { EpaProvider } from './context.jsx';
import './bootstrap-scoped.css';
import './epa.css';

export default function EpaPortal() {
  const { user } = useAuth();
  if (!user) return null;
  const profile = {
    subject: `django:${user.id}`,
    name: user.full_name || user.username,
    role: user.epa_role || 'client',
    token: getToken(),
  };
  return (
    <EpaProvider key={profile.subject} profile={profile} authScheme="Token" basePath="/epa">
      <EpaRoutes embedded />
    </EpaProvider>
  );
}
