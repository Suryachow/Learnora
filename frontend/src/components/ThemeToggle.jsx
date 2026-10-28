import { useTheme } from '../hooks/useTheme'

/** Switches between the light and dark token sets. */
export function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'

  return (
    <button
      type="button"
      className={`icon-btn theme-toggle ${className}`.trim()}
      onClick={toggleTheme}
      title={`Switch to ${next} theme`}
      aria-label={`Switch to ${next} theme`}
    >
      <span className="theme-toggle__icon" aria-hidden="true">
        {theme === 'dark' ? '☀' : '☾'}
      </span>
    </button>
  )
}

export default ThemeToggle
