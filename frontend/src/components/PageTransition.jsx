import { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * Replays a short entrance whenever the URL changes.
 *
 * The wrapper is never remounted: pages keep their state and their data, and
 * only the CSS animation restarts, which is what makes the navigation feel
 * like a transition instead of a reload.
 */
export function PageTransition({ children }) {
  const { pathname } = useLocation()
  const ref = useRef(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    node.classList.remove('route-enter')
    /* Reading layout forces the class removal to land before it is re-added. */
    void node.offsetWidth
    node.classList.add('route-enter')
  }, [pathname])

  return (
    <div ref={ref} className="route-shell">
      {children}
    </div>
  )
}

export default PageTransition
