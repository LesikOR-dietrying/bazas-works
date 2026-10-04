import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { labelForCode } from '../../lib/labels'
import { useUserOptions } from './hooks'
import { projectStatuses } from './types'
import type { Project } from './types'

export function ProjectsPage({ embedded = false }: { embedded?: boolean }) {
  const { data: user } = useSession(), users = useUserOptions()
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [responsible, setResponsible] = useState('')
  const [page, setPage] = useState(1), [sort, setSort] = useState('updated_at'), [direction, setDirection] = useState('desc')
  const params = new URLSearchParams({ q, page: String(page), sort, direction })
  if (status) params.set('status', status)
  if (responsible) params.set('responsible_user_id', responsible)
  const projects = useQuery({ queryKey: ['projects', params.toString()], queryFn: ({ signal }) => api<Page<Project>>(`/projects?${params}`, { signal }) })
  const canEdit = hasCapability(user, 'MANAGE_PROJECTS')
  return <><div className="page-heading"><div>{!embedded && <p className="eyebrow">РОБОЧИЙ ПРОСТІР</p>}<h1>{embedded ? 'R&D проєкти' : 'Проєкти'}</h1><p className="page-description">Учасники, гілки, задачі та перебіг роботи.</p></div>{canEdit && <Button asChild><Link to="/projects/new">Новий проєкт</Link></Button>}</div>
    <div className="filters"><Input aria-label="Пошук проєктів" placeholder="Пошук за назвою" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
      <select aria-label="Статус проєкту" className="form-input" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}><option value="">Усі статуси</option>{projectStatuses.map(s => <option key={s} value={s}>{labelForCode(s)}</option>)}</select>
      <select aria-label="Відповідальний" className="form-input" value={responsible} onChange={e => { setResponsible(e.target.value); setPage(1) }}><option value="">Усі відповідальні</option>{users.data?.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select>
      <select aria-label="Сортування проєктів" className="form-input" value={sort} onChange={e => { setSort(e.target.value); setPage(1) }}><option value="updated_at">За оновленням</option><option value="name">За назвою</option><option value="status">За статусом</option></select>
      <Button variant="outline" onClick={() => setDirection(direction === 'asc' ? 'desc' : 'asc')}>{direction === 'asc' ? '↑ За зростанням' : '↓ За спаданням'}</Button></div>
    <ErrorNotice error={projects.error || users.error} />{projects.isPending && <Loading />}
    {projects.data && <><div className="table-scroll"><table><thead><tr><th>Проєкт</th><th>Статус</th><th>Відповідальний</th><th>Оновлено</th></tr></thead><tbody>{projects.data.items.map(project => <tr key={project.id}><td><Link className="record-link" to={`/projects/${project.id}`}>{project.name}</Link></td><td><StatusBadge value={project.status} /></td><td>{project.responsible_name}</td><td>{new Date(project.updated_at).toLocaleDateString('uk-UA')}</td></tr>)}{!projects.data.items.length && <tr><td colSpan={4}>Проєктів не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={projects.data.total} pageSize={20} onChange={setPage} /></>}
  </>
}

