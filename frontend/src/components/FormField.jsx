/**
 * A labelled input. Every field has a visible label and, when there is a
 * problem, an error message that explains how to fix it. `trailing` sits inside
 * the control, pinned to the right - used for the show/hide password button.
 */
export function FormField({
  id,
  label,
  type = 'text',
  value,
  onChange,
  hint,
  error,
  autoComplete,
  required = true,
  trailing,
  ...rest
}) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [errorId, hintId].filter(Boolean).join(' ') || undefined

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className={`field__control ${trailing ? 'field__control--trailing' : ''}`.trim()}>
        <input
          id={id}
          name={id}
          type={type}
          className="field__input"
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          required={required}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy}
          {...rest}
        />
        {trailing}
      </div>
      {error ? (
        <span className="field__error" id={errorId}>
          {error}
        </span>
      ) : null}
      {hint ? (
        <span className="field__hint" id={hintId}>
          {hint}
        </span>
      ) : null}
    </div>
  )
}

export default FormField
