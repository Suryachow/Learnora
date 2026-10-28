import { useCallback, useEffect, useState } from 'react'

/**
 * The load / error / retry dance every page needs, in one place.
 *
 * Pass a `useCallback`-wrapped loader so the effect knows when to re-run:
 *
 *   const load = useCallback(() => fetchCourse(id), [id])
 *   const { data, loading, error, reload } = useFetch(load)
 */
export function useFetch(loader) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    loader()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((problem) => {
        if (!cancelled) setError(problem)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [loader, attempt])

  const reload = useCallback(() => setAttempt((value) => value + 1), [])

  return { data, loading, error, reload, setData }
}

export default useFetch
