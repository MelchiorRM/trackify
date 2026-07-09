import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'
import { DOMAINS, DOMAIN_ICONS } from '@/utils/constants'

export default function Home() {
  const user = useAuthStore((s) => s.user)

  if (!user) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center px-4 pt-24 text-center">
        <div className="mb-6 flex gap-3">
          {DOMAINS.map((domain) => {
            const Icon = DOMAIN_ICONS[domain]
            return (
              <span
                key={domain}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-accent-foreground"
              >
                <Icon className="h-5 w-5" />
              </span>
            )
          })}
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Trackify</h1>
        <p className="mt-4 max-w-md text-lg text-muted-foreground">
          Track what you watch, read, and listen to — all in one place.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Button asChild variant="outline" size="lg">
            <Link to="/login">Log in</Link>
          </Button>
          <Button asChild size="lg">
            <Link to="/register">Get started</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 pt-16">
      <h1 className="text-2xl font-semibold tracking-tight">Welcome back, {user.username}</h1>
      <Card className="mt-6">
        <CardContent className="pt-6 text-muted-foreground">
          Search, library, stats, and recommendations land in later phases — this dashboard is
          intentionally a stub for now.
        </CardContent>
      </Card>
    </div>
  )
}
