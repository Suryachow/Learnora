/** Buttons say what they do: "Sign in", "Subscribe", "Start task". */
export function Button({
  children,
  variant = 'primary',
  block = false,
  type = 'button',
  as: Component = 'button',
  className = '',
  ...rest
}) {
  const classes = ['btn', `btn--${variant}`, block ? 'btn--block' : '', className]
    .filter(Boolean)
    .join(' ')
  return (
    <Component type={Component === 'button' ? type : undefined} className={classes} {...rest}>
      {children}
    </Component>
  )
}

export default Button
