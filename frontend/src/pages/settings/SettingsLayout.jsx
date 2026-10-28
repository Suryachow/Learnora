import { NavLink, Link, Outlet } from 'react-router-dom'

import { Icon } from '../../components/Icon'
import { useAuth } from '../../hooks/useAuth'

const SECTIONS = [
  { to: 'profile', label: 'Profile', icon: 'user' },
  { to: 'security', label: 'Security', icon: 'lock' },
  { to: 'preferences', label: 'Preferences', icon: 'sliders' },
  { to: 'billing', label: 'Billing', icon: 'wallet' },
]

/** The shell shared by every account setting, with a sticky section menu. */
export function SettingsLayout() {
  const { user } = useAuth()
  const initial = (user?.name || user?.email || '?').trim().charAt(0).toUpperCase()

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Profile and settings</h1>
        <p>Manage your details, password, notifications and subscription in one place.</p>
      </header>

      <div className="settings-layout">
        <aside className="settings-side">
          <section className="settings-card">
            <span className="settings-card__avatar" aria-hidden="true">
              {initial}
            </span>
            <p className="settings-card__name">{user?.name}</p>
            <p className="settings-card__mail">{user?.email}</p>
            <div className="settings-card__badges">
              {user?.is_admin ? (
                <span className="badge badge--info">Admin</span>
              ) : (
                <span className="badge">Learner</span>
              )}
              <span className={user?.has_active_subscription ? 'badge badge--success' : 'badge'}>
                {user?.has_active_subscription ? 'Subscribed' : 'No plan yet'}
              </span>
            </div>
          </section>

          <nav className="settings-nav" aria-label="Settings sections">
            {SECTIONS.map((section) => (
              <NavLink key={section.to} className="settings-nav__link" to={section.to}>
                <Icon name={section.icon} />
                {section.label}
              </NavLink>
            ))}
          </nav>

          <div className="settings-help">
            <p>Good to know</p>
            <Link to="/rewards-policy">Rewards policy</Link>
            <Link to="/certificates">Certificates</Link>
            <Link to="/wallet">Wallet and ledger</Link>
          </div>
        </aside>

        <div className="stack settings-body">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export default SettingsLayout
