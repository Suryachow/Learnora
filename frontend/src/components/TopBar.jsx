import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { fetchCategories } from '../api/catalog'
import useFetch from '../hooks/useFetch'
import { useAuth } from '../hooks/useAuth'
import ThemeToggle from './ThemeToggle'
import { Icon, Sunburst } from './Icon'

/** The first path segment is the section the page belongs to. */
const SECTION_LABELS = {
  dashboard: 'Dashboard',
  courses: 'Courses',
  topics: 'Courses',
  tasks: 'Courses',
  wallet: 'Wallet',
  transactions: 'Transactions',
  certificates: 'Certificates',
  subscription: 'Subscription',
  settings: 'Settings',
  'rewards-policy': 'Rewards policy',
}

/**
 * The header above every page: where you are, a catalogue search that works
 * from anywhere, the category filter, the theme switch and the account menu.
 */
export function TopBar() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { user, signOut } = useAuth()
  const [term, setTerm] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const inputRef = useRef(null)

  const loadCategories = useCallback(() => fetchCategories(), [])
  const { data: categories } = useFetch(loadCategories)

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        inputRef.current?.focus()
      }
      if (event.key === 'Escape') {
        setFilterOpen(false)
        setAccountOpen(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  /* A menu that survives a navigation is a menu the user has to close twice. */
  useEffect(() => {
    setFilterOpen(false)
    setAccountOpen(false)
  }, [pathname])

  function submit(event) {
    event.preventDefault()
    const query = term.trim()
    navigate(query ? `/courses?search=${encodeURIComponent(query)}` : '/courses')
  }

  const initial = user?.name?.trim().charAt(0).toUpperCase() || 'U'
  const member = Boolean(user?.has_active_subscription)
  const section = SECTION_LABELS[pathname.split('/')[1]] ?? 'Learnora'
  const total = (categories ?? []).reduce((count, entry) => count + entry.course_count, 0)

  return (
    <header className="app-top">
      <div className="app-top__where">
        <Link className="app-top__brand" to="/dashboard" aria-label="Learnora dashboard">
          <Sunburst />
          <span>Learnora</span>
        </Link>
        <span className="app-top__crumb" aria-hidden="true">
          /
        </span>
        <p className="app-top__section">{section}</p>
      </div>

      <div className="app-top__tools">
        <form className="app-search" role="search" onSubmit={submit}>
          <Icon name="search" className="app-search__icon" />
          <input
            ref={inputRef}
            type="search"
            placeholder="Search the catalogue…"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            aria-label="Search the catalogue"
          />
          <kbd className="app-search__key">⌘K</kbd>
        </form>

        <div className="app-top__cluster">
          <div className="app-pop__wrap">
            <button
              className="app-top__icon"
              type="button"
              aria-label="Filter courses by category"
              aria-expanded={filterOpen}
              onClick={() => {
                setFilterOpen((open) => !open)
                setAccountOpen(false)
              }}
            >
              <Icon name="sliders" />
            </button>
            {filterOpen ? (
              <>
                <button
                  className="app-pop-backdrop"
                  type="button"
                  aria-label="Close filters"
                  onClick={() => setFilterOpen(false)}
                />
                <div className="app-pop" role="dialog" aria-label="Course categories">
                  <span className="app-pop__title">Category</span>
                  <button
                    className="app-pop__option"
                    type="button"
                    onClick={() => {
                      setFilterOpen(false)
                      navigate('/courses')
                    }}
                  >
                    All courses <span>{total}</span>
                  </button>
                  {(categories ?? []).map((entry) => (
                    <button
                      key={entry.name}
                      className="app-pop__option"
                      type="button"
                      onClick={() => {
                        setFilterOpen(false)
                        navigate(`/courses?category=${encodeURIComponent(entry.name)}`)
                      }}
                    >
                      {entry.name} <span>{entry.course_count}</span>
                    </button>
                  ))}
                </div>
              </>
            ) : null}
          </div>

          <span className="app-top__rule" aria-hidden="true" />

          <ThemeToggle className="app-top__icon" />
        </div>

        <div className="app-pop__wrap">
          <button
            className={`app-top__avatar${member ? ' is-member' : ''}`}
            type="button"
            aria-label="Your account"
            aria-haspopup="dialog"
            aria-expanded={accountOpen}
            onClick={() => {
              setAccountOpen((open) => !open)
              setFilterOpen(false)
            }}
          >
            {initial}
          </button>

          {accountOpen ? (
            <>
              <button
                className="app-pop-backdrop"
                type="button"
                aria-label="Close account menu"
                onClick={() => setAccountOpen(false)}
              />
              <div className="app-pop app-pop--account" role="dialog" aria-label="Your account">
                <div className="app-account__head">
                  <span className={`app-account__avatar${member ? ' is-member' : ''}`} aria-hidden="true">
                    {initial}
                  </span>
                  <span className="app-account__id">
                    <strong>{user?.name ?? 'Your account'}</strong>
                    <small>{user?.email ?? 'Signed in'}</small>
                  </span>
                </div>

                <p className={`app-account__plan${member ? ' is-member' : ''}`}>
                  <span className="app-account__dot" aria-hidden="true" />
                  {member ? 'Member' : 'Free plan'}
                </p>

                <div className="app-account__links">
                  <Link to="/settings/profile">
                    <Icon name="user" /> Profile
                  </Link>
                  <Link to="/subscription">
                    <Icon name="trend" /> Subscription
                  </Link>
                  <Link to="/wallet">
                    <Icon name="wallet" /> Wallet
                  </Link>
                </div>

                <button className="app-account__out" type="button" onClick={signOut}>
                  <Icon name="logout" /> Sign out
                </button>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </header>
  )
}

export default TopBar
