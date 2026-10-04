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
import { canEditEngineering } from './hooks'
import { setupStatuses } from './types'
import { labelForCode } from '../../lib/labels'
import type { Setup } from './types'

export function SetupsPage({ projectId }: { projectId?: string }) {
  const { data: user } = useSession()
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [page, setPage] = useState(1)
  const [sort, setSort] = useState('updated_at'), [direction, setDirection] = useState('desc')
  const params = new URLSearchParams({ q, page: String(page), sort, direction })
  if (status) params.set('status', status)
  if (projectId) params.set('project_id', projectId)
  const setups = useQuery({ queryKey: ['setups', params.toString()], enabled: canEditEngineering(user), queryFn: ({ signal }) => api<Page<Setup>>(`/setups?${params}`, { signal }) })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Конфігурації доступні інженерам, менеджерам та адміністраторам.')} />
  return <><div className="page-heading"><div><p className="eyebrow">КОНФІГУРАЦІЇ</p><h1>Сетапи</h1><p className="page-description">Версії бортів, склад і ревізії прошивки.</p></div><Button asChild><Link to="/setups/new">Новий сетап</Link></Button></div>
    <div className="filters"><Input aria-label="Пошук сетапів" placeholder="Пошук за назвою або версією" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} /><select aria-label="Статус сетапу" className="form-input" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}><option value="">Усі статуси</option>{setupStatuses.map(s => <option key={s} value={s}>{labelForCode(s)}</option>)}</select><select aria-label="Сортування сетапів" className="form-input" value={sort} onChange={e => { setSort(e.target.value); setPage(1) }}><option value="updated_at">За оновленням</option><option value="name">За назвою</option><option value="status">За статусом</option><option value="version">За версією</option></select><Button variant="outline" onClick={() => { setDirection(direction === 'asc' ? 'desc' : 'asc'); setPage(1) }}>{direction === 'asc' ? '↑ За зростанням' : '↓ За спаданням'}</Button></div>
    <ErrorNotice error={setups.error} />{setups.isPending && <Loading />}{setups.data && <><div className="table-scroll"><table><thead><tr><th>Сетап</th><th>Версія</th><th>Клас</th><th>Статус</th><th>Оновлено</th></tr></thead><tbody>{setups.data.items.map(item => <tr key={item.id}><td><Link className="record-link" to={`/setups/${item.id}`}>{item.name}</Link></td><td>{item.version}</td><td>{item.drone_class}</td><td><StatusBadge value={item.status} /></td><td>{new Date(item.updated_at).toLocaleDateString('uk-UA')}</td></tr>)}{!setups.data.items.length && <tr><td colSpan={5}>Сетапів не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={setups.data.total} pageSize={setups.data.page_size} onChange={setPage} /></>}
  </>
}

