import { Link, Outlet, useLocation } from 'react-router-dom'

import { AppRail } from './AppRail'
import { PageTransition } from './PageTransition'
import { TopBar } from './TopBar'
import { Sunburst } from './Icon'

/** Marketing and auth pages are drawn without the app rail. */
const BARE_ROUTES = new Set(['/', '/login', '/signup'])

/** In-page anchors, only worth showing on the landing page itself. */
const LANDING_LINKS = [
  { href: '#how-it-works', label: 'How it works' },
  { href: '#why', label: 'Features' },
  { href: '#catalogue', label: 'Courses' },
  { href: '#membership', label: 'Membership' },
  { href: '#rewards', label: 'Rewards' },
  { href: '#faq', label: 'FAQ' },
]

/** The mark, the landing anchors and the two entry points, before anyone signs in. */
function PublicHeader({ showActions, showNav }) {
  return (
    <header className="app-public">
      <Link className="app-public__brand" to="/">
        <Sunburst />
        <span>Learnora</span>
      </Link>

      {showNav ? (
        <nav className="app-public__nav" aria-label="Landing sections">
          {LANDING_LINKS.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
      ) : null}

      {showActions ? (
        <div className="app-public__actions">
          <Link className="btn btn--secondary" to="/login">
            Sign in
          </Link>
          <Link className="btn btn--primary" to="/signup">
            Create account
          </Link>
        </div>
      ) : null}
    </header>
  )
}

/** Persistent shell: canvas, floating rail, utility row, page body. */
export function AppLayout() {
  const { pathname } = useLocation()

  if (BARE_ROUTES.has(pathname)) {
    /* Auth screens are a single composition, so their canvas drops the page
       gutters and simply fills whatever height the header leaves over. */
    const authScreen = pathname === '/login' || pathname === '/signup'

    return (
      <div className="app-shell app-shell--bare">
        <div className="app-public-bar">
          <PublicHeader showActions={pathname === '/'} showNav={pathname === '/'} />
        </div>
        <main className={authScreen ? 'app-bare app-bare--auth' : 'app-bare'}>
          <PageTransition>
            <Outlet />
          </PageTransition>
        </main>
      </div>
    )
  }

  if (pathname === '/dashboard') {
    return (
      <div className="app-shell app-shell--dashboard">
        <PageTransition>
          <Outlet />
        </PageTransition>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <div className="app-frame">
        <AppRail />
        <div className="app-column">
          <TopBar />
          <main className="app-content">
            <PageTransition>
              <Outlet />
            </PageTransition>
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
