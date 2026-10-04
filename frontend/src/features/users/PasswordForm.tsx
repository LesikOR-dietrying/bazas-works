import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { send } from '../../api/client'
import { ErrorNotice, Field } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'

export function PasswordForm({ userId }: { userId: string }) {
  const [password, setPassword] = useState('')
  const mutation = useMutation({ mutationFn: () => send(`/users/${userId}/password`, 'POST', { password }), onSuccess: () => setPassword('') })
  return <form className="form-panel form-stack" onSubmit={event => { event.preventDefault(); if (window.confirm('Змінити пароль і завершити всі сесії цього користувача?')) mutation.mutate() }}>
    <h2>Зміна пароля</h2><Field label="Новий пароль (від 12 символів)"><Input type="password" minLength={12} maxLength={128} required autoComplete="new-password" value={password} onChange={event => setPassword(event.target.value)} /></Field>
    <ErrorNotice error={mutation.error} />{mutation.isSuccess && <p role="status">Пароль змінено. Попередні сесії завершено.</p>}<Button type="submit" disabled={mutation.isPending}>Змінити пароль</Button>
  </form>
}
