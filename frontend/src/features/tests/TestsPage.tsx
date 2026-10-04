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
import { canEditEngineering } from '../engineering/hooks'
import { testStatuses, testTypes } from './types'
import type { TestRecord } from './types'

export function TestsPage({ projectId, branchId, setupId, componentId, flightOnly = false }: { projectId?: string; branchId?: string; setupId?: string; componentId?: string; flightOnly?: boolean }) {
  const { data: user } = useSession()
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [testType, setTestType] = useState(''), [page, setPage] = useState(1)
  const [sort, setSort] = useState('test_date'), [direction, setDirection] = useState('desc')
  const params = new URLSearchParams({ q, page: String(page), sort, direction })
  if (status) params.set('status', status)
  if (testType) params.set('test_type', testType)
  if (projectId) params.set('project_id', projectId)
  if (branchId) params.set('branch_id', branchId)
  if (setupId) params.set('setup_id', setupId)
  if (componentId) params.set('component_id', componentId)
  if (flightOnly) params.set('test_type', 'FLIGHT')
  const tests = useQuery({ queryKey: ['tests', params.toString()], enabled: canEditEngineering(user), queryFn: ({ signal }) => api<Page<TestRecord>>(`/tests?${params}`, { signal }) })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Випробування доступні інженерам, менеджерам та адміністраторам.')} />
  const createParams = new URLSearchParams()
  if (projectId) createParams.set('project_id', projectId)
  if (branchId) createParams.set('branch_id', branchId)
  if (setupId) createParams.set('setup_id', setupId)
  if (componentId) createParams.set('component_id', componentId)
  if (flightOnly) createParams.set('test_type', 'FLIGHT')
  return <><div className="page-heading"><div><p className="eyebrow">ЛАБОРАТОРІЯ</p><h1>{flightOnly ? 'Польоти' : 'Випробування'}</h1><p className="page-description">Умови, обладнання, вимірювання та висновки.</p></div><Button asChild><Link to={`/tests/new${createParams.size ? `?${createParams}` : ''}`}>Нове випробування</Link></Button></div>
    <div className="filters"><Input aria-label="Пошук випробувань" placeholder="Пошук за назвою" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />{!flightOnly && <select aria-label="Тип випробування" className="form-input" value={testType} onChange={e => { setTestType(e.target.value); setPage(1) }}><option value="">Усі типи</option>{testTypes.map(type => <option key={type}>{type}</option>)}</select>}<select aria-label="Статус випробування" className="form-input" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}><option value="">Усі статуси</option>{testStatuses.map(value => <option key={value}>{value}</option>)}</select><select aria-label="Сортування випробувань" className="form-input" value={sort} onChange={e => { setSort(e.target.value); setPage(1) }}><option value="test_date">За датою тесту</option><option value="updated_at">За оновленням</option><option value="name">За назвою</option><option value="status">За статусом</option></select><Button variant="outline" onClick={() => { setDirection(direction === 'asc' ? 'desc' : 'asc'); setPage(1) }}>{direction === 'asc' ? '↑ За зростанням' : '↓ За спаданням'}</Button></div>
    <ErrorNotice error={tests.error} />{tests.isPending && <Loading />}{tests.data && <><div className="table-scroll"><table><thead><tr><th>Випробування</th><th>Тип</th><th>Статус</th><th>Дата</th><th>Сетап</th></tr></thead><tbody>{tests.data.items.map(test => <tr key={test.id}><td><Link className="record-link" to={`/tests/${test.id}`}>{test.name}</Link></td><td>{test.test_type}</td><td><StatusBadge value={test.status} /></td><td>{test.test_date ? new Date(test.test_date).toLocaleString('uk-UA') : 'Заплановано'}</td><td>{test.setup_id ? <Link className="record-link" to={`/setups/${test.setup_id}`}>{test.setup_name || test.setup_id}</Link> : '—'}</td></tr>)}{!tests.data.items.length && <tr><td colSpan={5}>Випробувань не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={tests.data.total} pageSize={tests.data.page_size} onChange={setPage} /></>}
  </>
}

