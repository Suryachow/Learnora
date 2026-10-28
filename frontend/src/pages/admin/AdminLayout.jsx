import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import ThemeToggle from '../../components/ThemeToggle'
import { PageTransition } from '../../components/PageTransition'
import { Icon, Sunburst } from '../../components/Icon'
import { useAuth } from '../../hooks/useAuth'

const LINKS = [
  { to: '/admin', label: 'Overview', icon: 'grid', end: true },
  { to: '/admin/users', label: 'Users', icon: 'user' },
  { to: '/admin/courses', label: 'Courses & topics', icon: 'book' },
  { to: '/admin/tasks', label: 'Tasks & quizzes', icon: 'award' },
  { to: '/admin/settings', label: 'Settings', icon: 'settings' },
]

const GROUP = { title: 'Console', items: LINKS.slice(0, 1) }
const GROUPS = [
  GROUP,
  { title: 'Manage', items: LINKS.slice(1, 4) },
  { title: 'Configure', items: LINKS.slice(4) },
]

/** The admin console shell. Sits outside the learner layout on purpose. */
export function AdminLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [open, setOpen] = useState(false)

  const current =
    LINKS.slice()
      .reverse()
      .find((link) => (link.end ? location.pathname === link.to : location.pathname.startsWith(link.to)))
      ?.label ?? 'Admin'

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar" data-open={open}>
        <Link className="admin-sidebar__brand" to="/dashboard">
          <span aria-hidden="true">
            <Sunburst />
          </span>
          <span>
            Learnora
            <small>Admin console</small>
          </span>
        </Link>

        {GROUPS.map((group) => (
          <div key={group.title}>
            <p className="admin-sidebar__group-label">{group.title}</p>
            <nav className="stack" aria-label={group.title} style={{ gap: '2px' }}>
              {group.items.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  className="admin-sidebar__link"
                  onClick={() => setOpen(false)}
                >
                  <Icon name={link.icon} />
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}

        <div className="admin-sidebar__foot">
          <Link className="admin-sidebar__link" to="/dashboard">
            <Icon name="grid" />
            Back to Learnora
          </Link>
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => {
              signOut()
              navigate('/')
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      {open ? (
        <button
          className="admin-sidebar__backdrop"
          type="button"
          aria-label="Close console menu"
          onClick={() => setOpen(false)}
        />
      ) : null}

      <div className="admin-main">
        <header className="admin-topbar">
          <div className="row" style={{ alignItems: 'center', gap: 'var(--space-3)' }}>
            <button
              type="button"
              className="icon-btn admin-sidebar__toggle"
              aria-label="Toggle console menu"
              aria-expanded={open}
              onClick={() => setOpen((value) => !value)}
            >
              ☰
            </button>
            <strong>{current}</strong>
          </div>

          <div className="row" style={{ alignItems: 'center', gap: 'var(--space-3)' }}>
            <span className="card__subtitle">{user?.email}</span>
            <ThemeToggle />
          </div>
        </header>

        <main className="admin-content">
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    </div>
  )
}

export default AdminLayout
