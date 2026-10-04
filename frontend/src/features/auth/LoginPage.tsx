import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { send } from '../../api/client'
import { ErrorNotice, Field } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { userSchema } from './types'
import { useSession } from './useSession'
import { replaceSession } from './sessionCache'

const schema = z.object({ username: z.string().trim().min(1, 'Вкажіть логін').max(320), password: z.string().min(1, 'Вкажіть пароль').max(128) })
type Values = z.infer<typeof schema>

export function LoginPage() {
  const session = useSession()
  const cache = useQueryClient()
  const navigate = useNavigate()
  const form = useForm<Values>({ resolver: zodResolver(schema) })
  const mutation = useMutation({ mutationFn: async (values: Values) => userSchema.parse(await send('/auth/login', 'POST', values)),
    onSuccess: async (user) => { await replaceSession(cache, user); navigate('/', { replace: true }) } })
  if (session.data) return <Navigate to="/" replace />
  return <main className="login-page"><section className="login-card"><p className="eyebrow">BAZA · ВНУТРІШНЯ СИСТЕМА</p>
    <h1>Вхід до робочого простору</h1><p className="page-description">Увійдіть за обліковим записом, створеним адміністратором.</p>
    <form onSubmit={form.handleSubmit(values => mutation.mutate(values))} className="form-stack">
      <Field label="Логін" error={form.formState.errors.username?.message}><Input autoComplete="username" {...form.register('username')} /></Field>
      <Field label="Пароль" error={form.formState.errors.password?.message}><Input type="password" autoComplete="current-password" {...form.register('password')} /></Field>
      <ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Входимо…' : 'Увійти'}</Button>
    </form></section></main>
}
