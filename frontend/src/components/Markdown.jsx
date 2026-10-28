import { Fragment } from 'react'

/**
 * A deliberately small markdown renderer for topic material.
 *
 * It builds React elements and never raw HTML, so course content can never
 * inject markup into the page. Supported: fenced code blocks, #..#### headings,
 * "- " bullets, "1." numbered lists, **bold** and `inline code`.
 */
const INLINE_PATTERN = /(\*\*[^*]+\*\*|`[^`]+`)/g

function renderInline(text, keyPrefix) {
  return text
    .split(INLINE_PATTERN)
    .filter(Boolean)
    .map((part, index) => {
      const key = `${keyPrefix}-${index}`

      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={key}>{part.slice(2, -2)}</strong>
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={key}>{part.slice(1, -1)}</code>
      }
      return <Fragment key={key}>{part}</Fragment>
    })
}

const BULLET = /^\s*[-*]\s+(.*)$/
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/
const HEADING = /^(#{1,4})\s+(.*)$/
const FENCE = /^\s*```/

function startsBlock(line) {
  return (
    line.trim() === '' ||
    FENCE.test(line) ||
    HEADING.test(line) ||
    BULLET.test(line) ||
    NUMBERED.test(line)
  )
}

export function Markdown({ children }) {
  const lines = String(children ?? '')
    .replace(/\r\n/g, '\n')
    .split('\n')

  const blocks = []
  let index = 0
  let blockKey = 0

  while (index < lines.length) {
    const line = lines[index]

    if (line.trim() === '') {
      index += 1
      continue
    }

    if (FENCE.test(line)) {
      const code = []
      index += 1
      while (index < lines.length && !FENCE.test(lines[index])) {
        code.push(lines[index])
        index += 1
      }
      index += 1
      blocks.push(
        <pre key={`block-${blockKey}`} className="prose__code">
          <code>{code.join('\n')}</code>
        </pre>,
      )
      blockKey += 1
      continue
    }

    const heading = HEADING.exec(line)
    if (heading) {
      // Topic content starts at "##", so it nests under the page's own <h1>.
      const Tag = `h${Math.min(heading[1].length + 1, 4)}`
      blocks.push(
        <Tag key={`block-${blockKey}`}>{renderInline(heading[2], `h-${blockKey}`)}</Tag>,
      )
      blockKey += 1
      index += 1
      continue
    }

    if (BULLET.test(line)) {
      const items = []
      while (index < lines.length && BULLET.test(lines[index])) {
        items.push(BULLET.exec(lines[index])[1])
        index += 1
      }
      blocks.push(
        <ul key={`block-${blockKey}`} className="prose__list">
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInline(item, `ul-${blockKey}-${itemIndex}`)}</li>
          ))}
        </ul>,
      )
      blockKey += 1
      continue
    }

    if (NUMBERED.test(line)) {
      const items = []
      while (index < lines.length && NUMBERED.test(lines[index])) {
        items.push(NUMBERED.exec(lines[index])[1])
        index += 1
      }
      blocks.push(
        <ol key={`block-${blockKey}`} className="prose__list">
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInline(item, `ol-${blockKey}-${itemIndex}`)}</li>
          ))}
        </ol>,
      )
      blockKey += 1
      continue
    }

    const paragraph = []
    while (index < lines.length && !startsBlock(lines[index])) {
      paragraph.push(lines[index].trim())
      index += 1
    }
    blocks.push(
      <p key={`block-${blockKey}`}>{renderInline(paragraph.join(' '), `p-${blockKey}`)}</p>,
    )
    blockKey += 1
  }

  return <div className="prose">{blocks}</div>
}

export default Markdown
