import { Link } from 'react-router-dom'

import { useReveal } from '../hooks/useReveal'

const SECTIONS = [
  { id: 'eligibility', label: 'Eligibility' },
  { id: 'pass-criteria', label: 'Pass criteria' },
  { id: 'limits', label: 'Limits' },
  { id: 'schedule', label: 'Payment schedule' },
  { id: 'revenue', label: 'Revenue is not profit' },
]

const SUMMARY = [
  'Read and watch for free.',
  'Pass a task while subscribed to earn its reward once.',
  'Pending rewards finalise, then count towards your balance.',
  'Amounts, limits and eligibility can change — rewards can be paused.',
]

/**
 * Straight answers about eligibility, limits and timing. The platform must not
 * promise rewards it cannot reliably pay, so this page states the rules plainly
 * and says that rewards can be paused.
 */
export function RewardsPolicyPage() {
  const revealRef = useReveal()

  return (
    <div className="stack" ref={revealRef}>
      <header className="page-header">
        <h1>Rewards Policy</h1>
        <p>
          How rewards work, who is eligible, and what happens if the platform has to pause them.
        </p>
      </header>

      <div className="policy-layout">
        <nav className="policy-nav" aria-label="Policy sections">
          <p className="policy-nav__title">On this page</p>
          {SECTIONS.map((section) => (
            <a key={section.id} href={`#${section.id}`}>
              {section.label}
            </a>
          ))}
        </nav>

        <div className="policy-body">
          <section className="card policy-summary" data-reveal>
            <h2 className="card__title">The short version</h2>
            <ul className="prose__list">
              {SUMMARY.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            <p className="card__subtitle">
              The full rules below are the ones that apply. Where they and the summary differ, the
              detailed section wins.
            </p>
          </section>

          <section className="card" id="eligibility" data-reveal>
            <h2 className="card__title">Eligibility</h2>
            <ul className="prose__list">
              <li>You must have an active subscription at the moment you pass a task.</li>
              <li>
                The reward is credited to the account that submitted the attempt. Accounts cannot
                share or transfer rewards.
              </li>
              <li>Each task pays once per account, the first time you pass it.</li>
              <li>Only published, active tasks listed on the site are eligible.</li>
            </ul>
          </section>

          <section className="card" id="pass-criteria" data-reveal>
            <h2 className="card__title">Pass criteria</h2>
            <ul className="prose__list">
              <li>Every task shows its own pass mark, for example 70% of the available marks.</li>
              <li>
                Answers are graded on the server. The browser never receives the correct answers.
              </li>
              <li>If you do not pass, nothing is credited and you can try again after the cooldown.</li>
              <li>Attempts and results are recorded so both you and we can review them.</li>
            </ul>
          </section>

          <section className="card" id="limits" data-reveal>
            <h2 className="card__title">Limits</h2>
            <ul className="prose__list">
              <li>Rewards are capped per task and per day, per account.</li>
              <li>
                Your current daily limit is shown on the <Link to="/wallet">Wallet</Link> page, so
                you always know where you stand.
              </li>
              <li>Submissions are rate-limited and have a cooldown between attempts on the same task.</li>
            </ul>
          </section>

          <section className="card" id="schedule" data-reveal>
            <h2 className="card__title">Payment schedule</h2>
            <ul className="prose__list">
              <li>
                A reward appears immediately as <strong>pending</strong> and moves to{' '}
                <strong>completed</strong> once it is finalised.
              </li>
              <li>
                Your wallet balance counts completed rewards only, and is always computed from the
                ledger.
              </li>
              <li>Payouts are handled by a separate payments team, which may batch them on a schedule.</li>
              <li>Rewards are not a wage, a salary, or a guaranteed income.</li>
            </ul>
          </section>

          <section className="card card--highlight" id="revenue" data-reveal>
            <h2 className="card__title">Revenue is not profit</h2>
            <p>
              Rewards are funded by subscriptions and other revenue. That revenue also has to cover
              payment-processing fees, hosting, content creation, support, marketing and taxes. Money
              coming in is not the same as money left over.
            </p>
            <p className="card__subtitle">
              Because of that, reward amounts, limits and eligibility can change, and rewards can be
              paused. If they are paused, the switch is shown in your wallet and on this page states
              the rules that apply at the time.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}

export default RewardsPolicyPage
