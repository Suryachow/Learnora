import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import ThemeToggle from './ThemeToggle'
import { Icon, Sunburst } from './Icon'

/**
 * Navigation is grouped the way a learner thinks about the product: the work,
 * the money it earns, and the account behind both.
 */
const GROUPS = [
  {
    label: 'Learn',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: 'grid' },
      // Topics, tasks and quizzes all hang off the catalogue, so they keep Courses lit.
      { to: '/courses', label: 'Courses', icon: 'book', match: ['/courses', '/topics', '/tasks'] },
    ],
  },
  {
    label: 'Rewards',
    items: [
      { to: '/wallet', label: 'Wallet', icon: 'wallet' },
      { to: '/transactions', label: 'Transactions', icon: 'swap' },
      { to: '/certificates', label: 'Certificates', icon: 'award' },
      { to: '/subscription', label: 'Subscription', icon: 'trend' },
    ],
  },
  {
    label: 'Account',
    items: [
      { to: '/rewards-policy', label: 'Rewards policy', icon: 'info' },
      { to: '/settings/profile', label: 'Settings', icon: 'settings', match: ['/settings'] },
    ],
  },
]

/**
 * The one sidebar every signed-in page shares: same width, labels, active
 * states and foot on every route. Below 900px it folds into a bottom dock.
 */
export function AppRail() {
  const { user, signOut } = useAuth()
  const { pathname } = useLocation()

  const isActive = (item) =>
    (item.match ?? [item.to]).some(
      (base) => pathname === base || pathname.startsWith(`${base}/`),
    )
  const initial = user?.name?.trim().charAt(0).toUpperCase() || 'U'
  const member = Boolean(user?.has_active_subscription)

  const groups = user?.is_admin
    ? GROUPS.map((group) =>
        group.label === 'Account'
          ? {
              ...group,
              items: [
                ...group.items,
                { to: '/admin', label: 'Admin console', icon: 'shield', admin: true },
              ],
            }
          : group,
      )
    : GROUPS

  return (
    <aside className="app-rail" aria-label="Learnora navigation">
      <Link className="app-rail__brand" to="/dashboard">
        <span className="app-rail__mark">
          <Sunburst />
        </span>
        <span className="app-rail__brand-copy">
          <strong>Learnora</strong>
          <small>Learn · prove · earn</small>
        </span>
      </Link>

      <nav className="app-rail__nav" aria-label="Main navigation">
        {groups.map((group) => (
          <div className="app-rail__group" key={group.label}>
            <p className="app-rail__caption">{group.label}</p>
            {group.items.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`app-rail__link${isActive(item) ? ' is-active' : ''}${
                  item.admin ? ' is-admin' : ''
                }`}
                aria-label={item.label}
                aria-current={isActive(item) ? 'page' : undefined}
              >
                <Icon name={item.icon} />
                <span className="app-rail__label">{item.label}</span>
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="app-rail__foot">
        <Link className="app-rail__me" to="/settings/profile" aria-label="Your profile">
          <span className={`app-rail__avatar${member ? ' is-member' : ''}`} aria-hidden="true">
            {initial}
          </span>
          <span className="app-rail__who">
            <strong>{user?.name ?? 'Your account'}</strong>
            <small className={member ? 'is-member' : undefined}>
              {member ? 'Member' : 'Free plan'}
            </small>
          </span>
          <Icon name="arrow" className="app-rail__go" />
        </Link>

        <div className="app-rail__actions">
          <ThemeToggle />
          <button className="icon-btn" type="button" onClick={signOut} title="Sign out" aria-label="Sign out">
            <Icon name="logout" />
          </button>
        </div>
      </div>
    </aside>
  )
}

export default AppRail
