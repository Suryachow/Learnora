/** A labelled on/off control for boolean settings. */
export function Switch({ id, checked, onChange, label, hint, disabled = false }) {
  return (
    <div className="stack">
      <label className="switch" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          disabled={disabled}
        />
        <span className="switch__control" aria-hidden="true" />
        <span className="switch__label">{label}</span>
      </label>
      {hint ? <span className="field__hint">{hint}</span> : null}
    </div>
  )
}

export default Switch
