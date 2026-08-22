import { Link } from 'react-router-dom'

// Matches the backend's mention_service.MENTION_RE (UserRegister.username's
// min_length=3, max_length=32). The negative lookbehind keeps something like
// "jane@example.com" from rendering as a mention of "example".
const MENTION_RE = /(?<!\w)@(\w{3,32})/g

export function renderMentions(body) {
  if (!body) return body

  const parts = []
  let lastIndex = 0
  let match

  MENTION_RE.lastIndex = 0
  while ((match = MENTION_RE.exec(body)) !== null) {
    if (match.index > lastIndex) {
      parts.push(body.slice(lastIndex, match.index))
    }
    const username = match[1]
    parts.push(
      <Link key={match.index} to={`/profile/${username}`} className="text-primary hover:underline">
        @{username}
      </Link>,
    )
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < body.length) {
    parts.push(body.slice(lastIndex))
  }
  return parts
}
