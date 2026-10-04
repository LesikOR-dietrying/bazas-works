import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { send } from '../../api/client'
import { ErrorNotice, Field } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { roleCodes, roleLabels } from '../auth/types'
import type { User } from '../auth/types'

const schema = z.object({ full_name: z.string().trim().min(1, 'Вкажіть ім’я').max(255), username: z.string().trim().min(1, 'Вкажіть логін').max(320).regex(/^\S+$/, 'Логін не може містити пробіли'), email: z.string().trim().email('Некоректний email').or(z.literal('')),
  roles: z.array(z.enum(roleCodes)), is_active: z.boolean(), password: z.string().max(128) })
type Values = z.infer<typeof schema>

export function UserForm({ user, onSaved, onCancel }: { user?: User; onSaved: () => void; onCancel: () => void }) {
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: {
    full_name: user?.full_name ?? '', username: user?.username ?? '', email: user?.email ?? '', roles: user?.roles ?? [], is_active: user?.is_active ?? true, password: '',
  } })
  const mutation = useMutation({ mutationFn: async (values: Values) => {
    if (user) {
      const { password: _password, ...data } = values
      void _password
      await send(`/users/${user.id}`, 'PATCH', { ...data, email: data.email || null })
    } else { const { is_active: _active, ...data } = values; void _active; await send('/users', 'POST', { ...data, email: data.email || null }) }
  }, onSuccess: onSaved })
  const submit = (values: Values) => {
    if (!user && values.password.length < 12) { form.setError('password', { message: 'Мінімум 12 символів' }); return }
    if (user?.is_active && !values.is_active && !window.confirm('Деактивувати користувача? Його сесії будуть завершені.')) return
    mutation.mutate(values)
  }
  return <section className="form-panel"><h2>{user ? 'Редагувати користувача' : 'Новий користувач'}</h2><form className="form-stack" onSubmit={form.handleSubmit(submit)}>
    <Field label="Ім’я та прізвище" error={form.formState.errors.full_name?.message}><Input {...form.register('full_name')} /></Field>
    <Field label="Логін" error={form.formState.errors.username?.message}><Input autoComplete="username" {...form.register('username')} /></Field>
    <Field label="Email (необов’язково)" error={form.formState.errors.email?.message}><Input type="email" {...form.register('email')} /></Field>
    <fieldset className="form-stack"><legend>Ролі</legend>{roleCodes.map(role => <label key={role}><input type="checkbox" value={role} {...form.register('roles')} /> {roleLabels[role]}</label>)}</fieldset>
    {user ? <label><input type="checkbox" {...form.register('is_active')} /> Активний обліковий запис</label> :
      <Field label="Початковий пароль" error={form.formState.errors.password?.message}><Input type="password" autoComplete="new-password" {...form.register('password')} /></Field>}
    <ErrorNotice error={mutation.error} /><div className="form-actions"><Button type="submit" disabled={mutation.isPending}>Зберегти</Button><Button variant="outline" onClick={onCancel}>Скасувати</Button></div>
  </form></section>
}
