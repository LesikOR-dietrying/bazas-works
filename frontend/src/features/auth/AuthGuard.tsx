import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link, Navigate, Outlet } from 'react-router-dom'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { useSession } from './useSession'
import { replaceSession } from './sessionCache'
import { hasCapability } from './types'

export function AuthGuard() {
  const session = useSession()
  const cache = useQueryClient()
  useEffect(() => {
    const expired = () => { void replaceSession(cache, null) }
    window.addEventListener('baza:unauthorized', expired)
    return () => window.removeEventListener('baza:unauthorized', expired)
  }, [cache])
  if (session.isPending) return <Loading />
  if (session.isError) return <div className="auth-panel"><ErrorNotice error={session.error} /><Button onClick={() => void session.refetch()}>Повторити</Button></div>
  return session.data ? <Outlet /> : <Navigate to="/login" replace />
}

export function AdminGuard() {
  return <CapabilityGuard anyOf={['ADMIN_USERS']} />
}

export function CapabilityGuard({ anyOf }: { anyOf: readonly import('./types').Capability[] }) {
  const session = useSession()
  if (anyOf.some(capability => hasCapability(session.data, capability))) return <Outlet />
  return <section className="empty-state access-denied" role="alert"><h1>Доступ обмежено</h1><p>У вашої ролі немає дозволу на перегляд цього розділу.</p><Link className="record-link" to="/">Повернутися на головну</Link></section>
}
