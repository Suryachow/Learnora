import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import * as catalogApi from '../api/catalog'
import Alert from '../components/Alert'
import Amount from '../components/Amount'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'
import { Loading } from '../components/Spinner'
import useFetch from '../hooks/useFetch'
import { LEVEL_LABELS, formatDuration } from '../utils/course'

/** Browse the whole catalogue, filter by category, or search by keyword. */
export function CoursesPage() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const search = params.get('search') ?? ''
  const [searchInput, setSearchInput] = useState(search)
  const pushed = useRef(search)

  // The top bar navigates with `?search=`, so the field follows the URL.
  useEffect(() => {
    if (search === pushed.current) return
    pushed.current = search
    setSearchInput(search)
  }, [search])

  // Type, pause, and the query lands in the URL: one request per pause, a
  // shareable address and a back button that works.
  useEffect(() => {
    const timer = setTimeout(() => {
      const trimmed = searchInput.trim()
      if (trimmed === search) return
      pushed.current = trimmed
      setParams(
        (current) => {
          const next = new URLSearchParams(current)
          if (trimmed) next.set('search', trimmed)
          else next.delete('search')
          return next
        },
        { replace: true },
      )
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput, search, setParams])

  const setCategory = useCallback(
    (value) => {
      setParams((current) => {
        const next = new URLSearchParams(current)
        if (value) next.set('category', value)
        else next.delete('category')
        return next
      })
    },
    [setParams],
  )

  const clearFilters = useCallback(() => {
    setSearchInput('')
    setParams({})
  }, [setParams])

  const loadCourses = useCallback(
    () => catalogApi.fetchCourses({ category, search }),
    [category, search],
  )
  const loadCategories = useCallback(() => catalogApi.fetchCategories(), [])

  const { data: courses, loading, error, reload } = useFetch(loadCourses)
  const { data: categories } = useFetch(loadCategories)

  const filtering = Boolean(category || search)
  const categoryOptions = [{ name: 'All categories', value: '' }].concat(
    (categories ?? []).map((item) => ({
      name: `${item.name} (${item.course_count})`,
      value: item.name,
    })),
  )

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Courses and categories</h1>
        <p>
          A free course is open to read. A subscription unlocks the assessments that pay rewards,
          and a paid course unlocks everything for one price.
        </p>
      </header>

      <div className="toolbar">
        <div className="chips" role="group" aria-label="Filter courses by category">
          {categoryOptions.map((option) => (
            <button
              key={option.value || 'all'}
              type="button"
              className="chip"
              aria-pressed={category === option.value}
              onClick={() => setCategory(option.value)}
            >
              {option.name}
            </button>
          ))}
        </div>

        <div className="search">
          <label className="sr-only" htmlFor="course-search">
            Search courses
          </label>
          <input
            id="course-search"
            type="search"
            className="field__input"
            placeholder="Search by title, topic or category"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </div>
      </div>

      <Alert>{error?.message}</Alert>

      {loading ? <Loading label="Loading the catalogue…" /> : null}

      {!loading && courses ? (
        <p className="catalogue-line">
          {filtering
            ? `${courses.length} ${courses.length === 1 ? 'course matches' : 'courses match'} your filters — clear them to see the whole catalogue`
            : `${courses.length} ${courses.length === 1 ? 'course' : 'courses'} in the catalogue — free ones are open to read`}
        </p>
      ) : null}

      {!loading && courses?.length === 0 ? (
        <EmptyState
          title={filtering ? 'No courses match that filter' : 'No courses published yet'}
          action={
            filtering ? (
              <Button
                variant="secondary"
                onClick={clearFilters}
              >
                Clear filters
              </Button>
            ) : null
          }
        >
          {filtering
            ? 'Try a different category, or clear the filters to see everything.'
            : 'Courses appear here as soon as an administrator publishes them.'}
        </EmptyState>
      ) : null}

      <div className="course-grid" data-stagger>
        {(courses ?? []).map((course) => {
          const duration = formatDuration(course.duration_minutes)
          return (
            <Link key={course.id} className="course-card" to={`/courses/${course.id}`}>
              {course.cover_image_url ? (
                <img
                  className="course-card__cover"
                  src={course.cover_image_url}
                  alt=""
                  loading="lazy"
                />
              ) : null}

              <div className="course-card__tags">
                <span className="pill">{course.category}</span>
                <span className="pill pill--soft">
                  {LEVEL_LABELS[course.level] ?? course.level}
                </span>
                {duration ? <span className="pill pill--soft">{duration}</span> : null}
              </div>

              <h2 className="course-card__title">{course.title}</h2>
              <p className="course-card__desc">{course.description}</p>

              <div className="course-card__meta">
                <span>
                  {course.topic_count} {course.topic_count === 1 ? 'topic' : 'topics'}
                </span>
                <span>
                  {course.task_count} {course.task_count === 1 ? 'task' : 'tasks'}
                </span>
                {course.price_paise > 0 ? (
                  <Amount paise={course.price_paise} label="Course" compact />
                ) : (
                  <span>Free to read</span>
                )}
                {course.total_reward > 0 ? (
                  <Amount paise={course.total_reward} label="Earn up to" compact />
                ) : null}
              </div>
            </Link>
          )
        })}
      </div>

      {error ? (
        <Button variant="secondary" onClick={reload}>
          Try loading the catalogue again
        </Button>
      ) : null}
    </div>
  )
}

export default CoursesPage
