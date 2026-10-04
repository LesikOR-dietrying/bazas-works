import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Navigate, Outlet } from 'react-router-dom'
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
  const session = useSession()
  return hasCapability(session.data, 'ADMIN_USERS') ? <Outlet /> : <section className="empty-state"><h1>Доступ обмежено</h1><p>Цей розділ доступний адміністратору.</p></section>
}
