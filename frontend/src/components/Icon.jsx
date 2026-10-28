/** One stroke icon set (24px grid) and the Learnora sunburst mark. */

const ICONS = {
  grid: (
    <>
      <rect x="3.6" y="3.6" width="7" height="7" rx="2" />
      <rect x="13.4" y="3.6" width="7" height="7" rx="2" />
      <rect x="3.6" y="13.4" width="7" height="7" rx="2" />
      <rect x="13.4" y="13.4" width="7" height="7" rx="2" />
    </>
  ),
  book: (
    <>
      <path d="M4 18.4V6a2 2 0 0 1 2-2h11.4v14.4" />
      <path d="M4 18.4A2.6 2.6 0 0 1 6.6 15.8h10.8" />
      <path d="M8.2 7.6h5.4" />
    </>
  ),
  wallet: (
    <>
      <rect x="3" y="6" width="18" height="13" rx="3.6" />
      <path d="M3 10.6h18" />
      <circle cx="16.6" cy="14.9" r="1.1" />
    </>
  ),
  swap: (
    <>
      <path d="M4 8.6h12.4L13 5.2" />
      <path d="M20 15.4H7.6L11 18.8" />
    </>
  ),
  award: (
    <>
      <circle cx="12" cy="9" r="4.2" />
      <path d="M8.9 12.6 7 21l5-2.6L17 21l-1.9-8.4" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="8.4" />
      <path d="M12 11.2v5" />
      <path d="M12 8.1h.01" />
    </>
  ),
  sliders: (
    <>
      <path d="M4 7.6h8.6" />
      <path d="M17.2 7.6H20" />
      <path d="M4 16.4h3.4" />
      <path d="M12 16.4h8" />
      <circle cx="15" cy="7.6" r="2.1" />
      <circle cx="9.8" cy="16.4" r="2.1" />
    </>
  ),
  bell: (
    <>
      <path d="M12 4.2a5.4 5.4 0 0 0-5.4 5.4v3.6L5 16.8h14l-1.6-3.6V9.6A5.4 5.4 0 0 0 12 4.2Z" />
      <path d="M10 19.4a2 2 0 0 0 4 0" />
    </>
  ),
  shield: (
    <>
      <path d="M12 3.4 18.6 6v5.2c0 4.3-2.8 7.6-6.6 9.4-3.8-1.8-6.6-5.1-6.6-9.4V6L12 3.4Z" />
      <path d="m9.4 11.8 1.9 1.9 3.4-3.6" />
    </>
  ),
  arrow: (
    <>
      <path d="M4.6 12h12.8" />
      <path d="m12.4 7 5 5-5 5" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8.6" r="3.5" />
      <path d="M5.4 20c.6-3.2 3.2-5.2 6.6-5.2s6 2 6.6 5.2" />
    </>
  ),
  flame: (
    <path d="M12 3.6c2.9 3.1 5.2 5.5 5.2 8.9a5.2 5.2 0 0 1-10.4 0c0-1.8.8-3.2 2.1-4.6.5 1.2 1.1 1.9 1.9 2.3.5-2.2.4-4.2 1.2-6.6Z" />
  ),
  coins: (
    <>
      <ellipse cx="12" cy="6.6" rx="6.6" ry="2.8" />
      <path d="M5.4 6.6v4c0 1.5 2.9 2.8 6.6 2.8s6.6-1.3 6.6-2.8v-4" />
      <path d="M5.4 10.6v4c0 1.5 2.9 2.8 6.6 2.8s6.6-1.3 6.6-2.8v-4" />
    </>
  ),
  trend: (
    <>
      <path d="M4 16.4 9.2 11l3.4 3.2L20 7" />
      <path d="M15.4 7H20v4.6" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3.1" />
      <path d="M19.2 14.2a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.6 1h.2a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.6 1Z" />
    </>
  ),
  logout: (
    <>
      <path d="M9 4.6H6.6a2 2 0 0 0-2 2v10.8a2 2 0 0 0 2 2H9" />
      <path d="m14 8.4 3.6 3.6-3.6 3.6" />
      <path d="M9.6 12h7.6" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6.2" />
      <path d="m15.8 15.8 4.2 4.2" />
    </>
  ),
  plus: (
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>
  ),
  play: (
    <>
      <path d="M9.4 7.6v8.8l7-4.4-7-4.4Z" />
    </>
  ),
  check: (
    <path d="m5.6 12.8 4 4 8.8-9.6" />
  ),
  lock: (
    <>
      <rect x="4.8" y="10.4" width="14.4" height="9.8" rx="3" />
      <path d="M8.4 10.4V8a3.6 3.6 0 0 1 7.2 0v2.4" />
    </>
  ),
  spark: (
    <>
      <path d="M12 3.4 13.7 9l5.6 1.7-5.6 1.7L12 18l-1.7-5.6L4.7 10.7 10.3 9 12 3.4Z" />
      <path d="M18.6 16.4v3.4" />
      <path d="M16.9 18.1h3.4" />
    </>
  ),
}

export function Icon({ name, className = '' }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICONS[name]}
    </svg>
  )
}

/** The sunburst mark used in the header and on the admin console. */
export function Sunburst({ className = '' }) {
  const rays = Array.from({ length: 16 }, (_, index) => (index * 360) / 16)
  return (
    <svg
      className={className}
      viewBox="0 0 40 40"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      aria-hidden="true"
    >
      {rays.map((angle) => {
        const radians = (angle * Math.PI) / 180
        return (
          <line
            key={angle}
            x1={20 + Math.cos(radians) * 5.5}
            y1={20 + Math.sin(radians) * 5.5}
            x2={20 + Math.cos(radians) * 17}
            y2={20 + Math.sin(radians) * 17}
          />
        )
      })}
    </svg>
  )
}

export default Icon
