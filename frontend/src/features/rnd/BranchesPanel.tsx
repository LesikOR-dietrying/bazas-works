import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import type { UserOption } from '../auth/types'
import type { RndBranch } from './types'

export function BranchesPanel({ projectId, participants }: { projectId: string; participants: UserOption[] }) {
  const { data: user } = useSession(), cache = useQueryClient(), [open, setOpen] = useState(false)
  const [name, setName] = useState(''), [parentId, setParentId] = useState(''), [responsibleId, setResponsibleId] = useState(participants[0]?.id ?? '')
  const [purpose, setPurpose] = useState(''), [error, setError] = useState('')
  const branches = useQuery({ queryKey: ['rnd-branches', projectId], queryFn: ({ signal }) => api<RndBranch[]>(`/projects/${projectId}/branches`, { signal }) })
  const create = useMutation({ mutationFn: () => send<RndBranch>(`/projects/${projectId}/branches`, 'POST', { name: name.trim(), parent_id: parentId || null, responsible_user_id: responsibleId, purpose, change_summary: '', result_summary: '' }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['rnd-branches', projectId] }); setName(''); setParentId(''); setPurpose(''); setOpen(false) } })
  function submit(event: FormEvent) { event.preventDefault(); if (!name.trim() || !responsibleId) return setError('Вкажіть назву та відповідального.'); setError(''); create.mutate() }
  const canEdit = hasCapability(user, 'MANAGE_ENGINEERING')
  return <section className="form-panel"><div className="page-heading"><div><h2>Гілки R&D</h2><p className="page-description">Окремі напрями експериментів у межах проєкту.</p></div>{canEdit && <Button onClick={() => setOpen(value => !value)}>{open ? 'Скасувати' : 'Нова гілка'}</Button>}</div>
    {open && <form className="form-stack" onSubmit={submit}><div className="editor-grid"><Field label="Назва"><Input required value={name} onChange={event => setName(event.target.value)} /></Field><Field label="Батьківська гілка"><select className="form-input" value={parentId} onChange={event => setParentId(event.target.value)}><option value="">Головна гілка</option>{branches.data?.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Відповідальний"><select className="form-input" required value={responsibleId} onChange={event => setResponsibleId(event.target.value)}><option value="">Оберіть</option>{participants.map(person => <option key={person.id} value={person.id}>{person.full_name}</option>)}</select></Field></div><Field label="Мета гілки"><textarea className="form-input" value={purpose} onChange={event => setPurpose(event.target.value)} /></Field>{error && <ErrorNotice error={new Error(error)} />}<ErrorNotice error={create.error} /><Button type="submit" disabled={create.isPending}>Створити гілку</Button></form>}
    <ErrorNotice error={branches.error} />{branches.isPending && <Loading />}{branches.data && <div className="table-scroll"><table><thead><tr><th>Гілка</th><th>Батьківська</th><th>Відповідальний</th><th>Статус</th><th>Оновлено</th></tr></thead><tbody>{branches.data.map(branch => <tr key={branch.id}><td><Link className="record-link" to={`/rnd/branches/${branch.id}`}>{branch.name}</Link></td><td>{branch.parent_name || '—'}</td><td>{branch.responsible_name}</td><td><StatusBadge value={branch.status} /></td><td>{new Date(branch.updated_at).toLocaleDateString('uk-UA')}</td></tr>)}{!branches.data.length && <tr><td colSpan={5}>Гілок ще немає.</td></tr>}</tbody></table></div>}
  </section>
}
