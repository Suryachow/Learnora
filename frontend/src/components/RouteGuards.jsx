import { Navigate, useLocation } from 'react-router-dom'

import { Loading } from './Spinner'
import { useAuth } from '../hooks/useAuth'

/** Only signed-in users may see the wrapped page. */
export function ProtectedRoute({ children }) {
  const { user, status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return <Loading label="Checking your session…" />
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return children
}

/** Sign-in and sign-up pages: signed-in users go to their own home. */
export function RequireGuest({ children }) {
  const { user, status } = useAuth()

  if (status === 'loading') {
    return <Loading label="Checking your session…" />
  }

  if (user) {
    return <Navigate to={user.is_admin ? '/admin' : '/dashboard'} replace />
  }

  return children
}

/**
 * The admin console. The server refuses every admin route to a non-admin, so
 * this guard is only here to keep the UI honest.
 */
export function AdminRoute({ children }) {
  const { user, status } = useAuth()

  if (status === 'loading') {
    return <Loading label="Checking your session…" />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!user.is_admin) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default ProtectedRoute
