import { Link } from 'react-router-dom'

import { Icon } from '../components/Icon'
import { useAuth } from '../hooks/useAuth'

const CHECKS = [
  'The course you completed and every topic you passed.',
  'The date the final assessment was passed, in your name.',
  'A reference you can quote to an employer.',
  'Proof of learning only — rewards never appear on it.',
]

const STEPS = [
  {
    title: 'Pass every assessment',
    body: 'Each topic has its own assessment and pass mark. A certificate needs all of them.',
  },
  {
    title: 'The server issues it',
    body: 'Issuing happens after the final passing attempt is recorded, never from a button press.',
  },
  {
    title: 'Share the reference',
    body: 'You get a permanent reference and a page listing the topics behind it.',
  },
]

/**
 * Certificates are issued against completed assessments, which arrive with the
 * assessment engine. Until then this page explains exactly what will exist.
 */
export function CertificatesPage() {
  const { user } = useAuth()

  return (
    <div className="stack">
      <header className="page-header">
        <h1>Certificates</h1>
        <p>Proof of the assessments you have passed, ready to share with an employer.</p>
      </header>

      <div className="cert-layout">
        <section className="cert-hero">
          <span className="cert-hero__icon">
            <Icon name="award" />
          </span>
          <h2 className="cert-hero__title">No certificates yet</h2>
          <p className="cert-hero__body">
            Certificates are generated automatically once you pass the assessments in a course.
            Nothing is issued for watching a video on its own — the proof has to be earned, and the
            server is the only thing that can issue it.
          </p>
          <div className="cert-hero__actions">
            <Link className="btn btn--primary" to="/courses">
              Browse courses
              <Icon name="arrow" />
            </Link>
            <Link className="btn btn--secondary" to="/wallet">
              See your progress ledger
            </Link>
          </div>
        </section>

        <aside className="cert-side">
          <section className="card">
            <h2 className="card__title">What a certificate proves</h2>
            <ul className="cert-checklist">
              {CHECKS.map((item) => (
                <li key={item}>
                  <Icon name="check" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="card">
            <h2 className="card__title">Template preview</h2>
            <div className="cert-preview" aria-hidden="true">
              <div className="cert-preview__top">
                <span className="cert-preview__brand">LEARNORA</span>
                <span className="cert-preview__badge">Preview</span>
              </div>
              <div className="cert-preview__name">{user?.name ?? 'Name on certificate'}</div>
              <div className="cert-preview__meta">
                <span>Course completed</span>
                <span>Ref —</span>
              </div>
            </div>
            <p className="card__subtitle">
              The real certificate fills in the course, the completion date and the reference once
              every assessment is passed.
            </p>
          </section>
        </aside>
      </div>

      <section className="section">
        <div className="section__header">
          <h2 className="section__title">How they will work</h2>
          <p className="muted">One certificate per completed course.</p>
        </div>

        <div className="cert-steps" data-stagger>
          {STEPS.map((step, index) => (
            <article key={step.title} className="cert-step">
              <span className="cert-step__index">STEP {String(index + 1).padStart(2, '0')}</span>
              <h3 className="cert-step__title">{step.title}</h3>
              <p className="cert-step__body">{step.body}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

export default CertificatesPage
