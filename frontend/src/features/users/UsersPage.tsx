import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { roleCodes, roleLabels } from '../auth/types'
import type { User } from '../auth/types'
import { UserForm } from './UserForm'
import { PasswordForm } from './PasswordForm'

export function UsersPage() {
  const [q, setQ] = useState(''), [role, setRole] = useState(''), [active, setActive] = useState(''), [page, setPage] = useState(1)
  const [direction, setDirection] = useState('asc')
  const [selected, setSelected] = useState<User | 'new' | null>(null)
  const cache = useQueryClient()
  const params = new URLSearchParams({ q, page: String(page), direction })
  if (role) params.set('role', role)
  if (active) params.set('is_active', active)
  const users = useQuery({ queryKey: ['users', params.toString()], queryFn: ({ signal }) => api<Page<User>>(`/users?${params}`, { signal }) })
  const saved = () => { setSelected(null); void cache.invalidateQueries({ queryKey: ['users'] }); void cache.invalidateQueries({ queryKey: ['auth'] }); void cache.invalidateQueries({ queryKey: ['user-options'] }) }
  return <><div className="page-heading"><div><p className="eyebrow">АДМІНІСТРУВАННЯ</p><h1>Користувачі</h1></div><Button onClick={() => setSelected('new')}>Додати користувача</Button></div>
    <div className="filters"><Input aria-label="Пошук користувачів" placeholder="Ім’я, логін або email" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
      <select aria-label="Роль" className="form-input" value={role} onChange={e => { setRole(e.target.value); setPage(1) }}><option value="">Усі ролі</option>{roleCodes.map(r => <option key={r} value={r}>{roleLabels[r]}</option>)}</select>
      <select aria-label="Активність" className="form-input" value={active} onChange={e => { setActive(e.target.value); setPage(1) }}><option value="">Усі користувачі</option><option value="true">Активні</option><option value="false">Неактивні</option></select></div>
    <ErrorNotice error={users.error} />{users.isPending && <Loading />}
    {users.data && <><div className="table-scroll"><table><thead><tr><th><button onClick={() => setDirection(direction === 'asc' ? 'desc' : 'asc')}>Ім’я {direction === 'asc' ? '↑' : '↓'}</button></th><th>Логін</th><th>Email</th><th>Ролі</th><th>Стан</th><th>Дії</th></tr></thead><tbody>
      {users.data.items.map(user => <tr key={user.id}><td>{user.full_name}</td><td>{user.username}</td><td>{user.email ?? '—'}</td><td>{user.roles.length ? user.roles.map(role => roleLabels[role]).join(', ') : 'Без ролей'}</td><td>{user.is_active ? 'Активний' : 'Неактивний'}</td><td><Button variant="outline" onClick={() => setSelected(user)}>Редагувати</Button></td></tr>)}
      {!users.data.items.length && <tr><td colSpan={6}>Користувачів не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} pageSize={20} total={users.data.total} onChange={setPage} /></>}
    {selected && <div className="editor-grid"><UserForm key={selected === 'new' ? 'new' : selected.id} user={selected === 'new' ? undefined : selected} onSaved={saved} onCancel={() => setSelected(null)} />
      {selected !== 'new' && <PasswordForm key={selected.id} userId={selected.id} />}</div>}
  </>
}
