import type { QueryClient } from '@tanstack/react-query'
import type { User } from './types'

export async function replaceSession(cache: QueryClient, user: User | null) {
  await cache.cancelQueries()
  // Keep the auth query's observers so guards immediately see the new session.
  cache.setQueryData(['auth'], user)
  cache.removeQueries({ predicate: query => query.queryKey[0] !== 'auth' })
}
