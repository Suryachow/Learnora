import { useCallback, useEffect, useState } from 'react'

/**
 * Reveals `[data-reveal]` elements as they scroll into view.
 *
 * The returned ref is a callback ref, so a page that renders a loading state
 * before its content still gets picked up when the real tree mounts. A
 * MutationObserver catches content that arrives after that (courses, for
 * example), so late data does not stay invisible. Reduced motion shows
 * everything immediately.
 */
export function useReveal() {
  const [root, setRoot] = useState(null)
  const ref = useCallback((element) => setRoot(element), [])

  useEffect(() => {
    if (!root) return undefined

    const items = () => root.querySelectorAll('[data-reveal]')

    if (!('IntersectionObserver' in window)) {
      items().forEach((item) => item.classList.add('is-revealed'))
      return undefined
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      items().forEach((item) => item.classList.add('is-revealed'))
      return undefined
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          entry.target.classList.add('is-revealed')
          observer.unobserve(entry.target)
        }
      },
      { rootMargin: '0px 0px -6% 0px', threshold: 0.1 },
    )

    const scan = () => items().forEach((item) => observer.observe(item))

    scan()
    const mutations = new MutationObserver(scan)
    mutations.observe(root, { childList: true, subtree: true })

    return () => {
      observer.disconnect()
      mutations.disconnect()
    }
  }, [root])

  return ref
}

export default useReveal
