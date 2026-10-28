export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="loading" role="status">
      <Spinner />
      <span>{label}</span>
    </div>
  )
}

export default Loading
