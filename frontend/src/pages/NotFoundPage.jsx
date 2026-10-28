import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="form-card">
      <header className="page-header">
        <h1>Page not found</h1>
        <p>That link does not exist, or it may have been moved.</p>
      </header>
      <p>
        <Link className="btn btn--primary" to="/">
          Back to the home page
        </Link>
      </p>
    </div>
  )
}

export default NotFoundPage
