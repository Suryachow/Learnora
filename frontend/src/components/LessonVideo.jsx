import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import * as progressApi from '../api/progress'
import Alert from './Alert'
import Amount from './Amount'
import Badge from './Badge'
import { Loading } from './Spinner'

const API_SRC = 'https://www.youtube.com/iframe_api'
// Natural playback drift allowed between polls before a jump counts as a skip.
const FORWARD_TOLERANCE = 2
const POLL_MS = 250

let apiPromise = null

/** The YouTube player API is loaded once, however many lessons use it. */
function loadYouTubeApi() {
  if (apiPromise) return apiPromise

  apiPromise = new Promise((resolve) => {
    if (window.YT?.Player) {
      resolve(window.YT)
      return
    }
    const previous = window.onYouTubeIframeAPIReady
    window.onYouTubeIframeAPIReady = () => {
      previous?.()
      resolve(window.YT)
    }
    const script = document.createElement('script')
    script.src = API_SRC
    script.async = true
    document.head.appendChild(script)
  })

  return apiPromise
}

/** The 11-character video id, whichever YouTube URL shape it arrived in. */
export function youtubeId(url) {
  if (!url) return null
  const match = url.match(/(?:embed\/|watch\?v=|youtu\.be\/|shorts\/|\/v\/)([A-Za-z0-9_-]{11})/)
  return match ? match[1] : null
}

/**
 * The lesson video.
 *
 * Skipping ahead is refused: if playback jumps past the furthest point reached,
 * the player is pulled back and the learner is told why. Only reaching the end
 * counts, and only the server records it - the watch time is reported along with
 * the runtime so a lesson cannot be marked complete after a few seconds.
 */
export function LessonVideo({ topicId, title, url, completed = false, signedIn = true, onCompleted }) {
  const hostRef = useRef(null)
  const playerRef = useRef(null)
  const furthestRef = useRef(0)
  const warnedRef = useRef(false)
  const signedInRef = useRef(signedIn)
  // The lock follows the server's answer, so it releases the moment it is saved.
  const lockedRef = useRef(!completed)

  const [locked, setLocked] = useState(!completed)
  const [status, setStatus] = useState('loading')
  const [problem, setProblem] = useState('')
  const [warning, setWarning] = useState('')
  const [saving, setSaving] = useState(false)
  // Paid on the first finish only, so a re-watch shows nothing extra.
  const [earned, setEarned] = useState(0)

  signedInRef.current = signedIn

  const videoId = youtubeId(url)

  useEffect(() => {
    if (!videoId) {
      setStatus('error')
      setProblem('This lesson points at a video Learnora cannot play.')
      return undefined
    }

    let cancelled = false
    let poll = null

    async function saveCompletion(furthest, duration) {
      const watched = Math.round(furthest)

      if (!signedInRef.current) {
        setWarning(
          'You watched this lesson to the end. Sign in to save it and unlock the assessment.',
        )
        return
      }

      setSaving(true)
      try {
        const progress = await progressApi.completeVideo(topicId, {
          watchedSeconds: watched,
          durationSeconds: duration,
        })
        if (cancelled) return
        lockedRef.current = false
        setLocked(false)
        setWarning('')
        if (progress.reward_granted) setEarned(progress.reward_paise)
        onCompleted?.(progress)
      } catch (err) {
        if (!cancelled) setProblem(err.message)
      } finally {
        if (!cancelled) setSaving(false)
      }
    }

    function finish() {
      // Already recorded - re-watching a finished lesson must not post again.
      if (!lockedRef.current) return

      const player = playerRef.current
      const reported = Math.round(player?.getDuration?.() || 0)
      const duration = reported > 0 ? reported : Math.round(furthestRef.current)
      saveCompletion(furthestRef.current, duration)
    }

    function tick() {
      const player = playerRef.current
      if (!player?.getCurrentTime) return

      const current = player.getCurrentTime()
      if (!Number.isFinite(current)) return

      if (lockedRef.current && current > furthestRef.current + FORWARD_TOLERANCE) {
        player.seekTo(furthestRef.current, true)
        if (!warnedRef.current) {
          warnedRef.current = true
          setWarning('Skipping ahead is off. Watch the lesson through to the end to unlock it.')
        }
        return
      }

      if (current > furthestRef.current) furthestRef.current = current
    }

    loadYouTubeApi().then((YT) => {
      if (cancelled || !hostRef.current) return

      playerRef.current = new YT.Player(hostRef.current, {
        videoId,
        playerVars: { rel: 0, modestbranding: 1, playsinline: 1, origin: window.location.origin },
        events: {
          onReady: () => {
            if (cancelled) return
            setStatus('ready')
            // Only poll once the player is ready to answer.
            poll = window.setInterval(tick, POLL_MS)
          },
          onStateChange: (event) => {
            if (event.data === YT.PlayerState.ENDED) finish()
          },
        },
      })
    })

    return () => {
      cancelled = true
      if (poll) window.clearInterval(poll)
      playerRef.current?.destroy?.()
      playerRef.current = null
    }
    // The player is built once per video; the callbacks read their inputs from
    // refs so a re-render never tears it down and restarts playback.
  }, [videoId, topicId])

  return (
    <div className="stack">
      <div className="video-frame lesson-video">
        <div ref={hostRef} />
        {status === 'loading' ? <Loading label="Preparing the player…" /> : null}
      </div>

      <div className="lesson-video__status">
        {locked ? (
          <span className="lesson-video__lock">
            <Badge tone="neutral">Locked</Badge> Watch the whole lesson to unlock the assessment.
          </span>
        ) : (
          <span className="lesson-video__lock">
            <Badge tone="success">Watched</Badge> Lesson video completed.
          </span>
        )}
        {saving ? <span className="card__subtitle">Saving your progress…</span> : null}
        {earned > 0 ? <Amount paise={earned} label="Lesson reward" compact /> : null}
      </div>

      <Alert tone="warning">{warning}</Alert>
      <Alert>{problem}</Alert>

      {problem && !signedIn ? (
        <div className="row">
          <Link className="btn btn--primary" to="/login">
            Sign in
          </Link>
        </div>
      ) : null}
    </div>
  )
}

export default LessonVideo
