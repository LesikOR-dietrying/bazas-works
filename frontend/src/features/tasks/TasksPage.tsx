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
import { useProjectOptions, useUserOptions } from '../projects/hooks'
import { TaskBoard } from './TaskBoard'
import { taskStatuses, priorities, isOverdue } from './types'
import type { Task } from './types'

export function TasksPage({ projectId, branchId }: { projectId?: string; branchId?: string }) {
  const { data: user } = useSession(), users = useUserOptions(), projects = useProjectOptions()
  const [mine, setMine] = useState(!projectId), [view, setView] = useState<'table' | 'kanban'>('table')
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [priority, setPriority] = useState('')
  const [assignee, setAssignee] = useState(''), [project, setProject] = useState(''), [overdue, setOverdue] = useState(false)
  const [sort, setSort] = useState('updated_at'), [direction, setDirection] = useState('desc'), [page, setPage] = useState(1)
  const params = new URLSearchParams({ q, mine: String(mine), overdue: String(overdue), page: String(page), sort, direction })
  for (const [key, value] of Object.entries({ status, priority, assignee_id: assignee, project_id: projectId || project })) if (value) params.set(key, value)
  if (branchId) params.set('branch_id', branchId)
  const tasks = useQuery({ queryKey: ['tasks', params.toString()], queryFn: ({ signal }) => api<Page<Task>>(`/tasks?${params}`, { signal }) })
  const filter = (setter: (value: string) => void, value: string) => { setter(value); setPage(1) }
  const createParams = new URLSearchParams(); if (projectId) createParams.set('project_id', projectId); if (branchId) createParams.set('branch_id', branchId)
  return <><div className="page-heading"><div><h1>{branchId ? 'Задачі гілки' : projectId ? 'Задачі проєкту' : 'Задачі'}</h1><p className="page-description">Робота, виконавці та результати.</p></div>{hasCapability(user, 'MANAGE_TASKS') && <Button asChild><Link to={`/tasks/new${createParams.size ? `?${createParams}` : ''}`}>Нова задача</Link></Button>}</div>
    <div className="view-controls"><div className="tabs"><button className={mine ? 'selected' : ''} onClick={() => { setMine(true); setPage(1) }}>Мої задачі</button><button className={!mine ? 'selected' : ''} onClick={() => { setMine(false); setPage(1) }}>{!hasCapability(user, 'MANAGE_TASKS') ? 'Усі доступні' : 'Усі задачі'}</button></div><div className="form-actions"><Button variant={view === 'table' ? 'default' : 'outline'} onClick={() => setView('table')}>Таблиця</Button><Button variant={view === 'kanban' ? 'default' : 'outline'} onClick={() => setView('kanban')}>Kanban</Button></div></div>
    <div className="filters"><Input aria-label="Пошук задач" placeholder="Пошук за назвою" value={q} onChange={e => filter(setQ, e.target.value)} />
      <select aria-label="Статус задачі" className="form-input" value={status} onChange={e => filter(setStatus, e.target.value)}><option value="">Усі статуси</option>{taskStatuses.map(s => <option key={s}>{s}</option>)}</select>
      <select aria-label="Пріоритет" className="form-input" value={priority} onChange={e => filter(setPriority, e.target.value)}><option value="">Усі пріоритети</option>{priorities.map(p => <option key={p}>{p}</option>)}</select>
      <select aria-label="Виконавець" className="form-input" value={assignee} onChange={e => filter(setAssignee, e.target.value)}><option value="">Усі виконавці</option>{users.data?.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select>
      {!projectId && <select aria-label="Проєкт" className="form-input" value={project} onChange={e => filter(setProject, e.target.value)}><option value="">Усі проєкти</option>{projects.data?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select>}
      <select aria-label="Сортування задач" className="form-input" value={sort} onChange={e => filter(setSort, e.target.value)}><option value="updated_at">За оновленням</option><option value="deadline">За строком</option><option value="priority">За пріоритетом</option><option value="title">За назвою</option></select>
      <Button variant="outline" onClick={() => setDirection(direction === 'asc' ? 'desc' : 'asc')}>{direction === 'asc' ? '↑ За зростанням' : '↓ За спаданням'}</Button></div>
    <label className="checkbox-filter"><input type="checkbox" checked={overdue} onChange={e => { setOverdue(e.target.checked); setPage(1) }} /> Лише прострочені</label>
    <ErrorNotice error={tasks.error || users.error || projects.error} />{tasks.isPending && <Loading />}
    {tasks.data && <>{view === 'kanban' ? <TaskBoard tasks={tasks.data.items} /> : <div className="table-scroll"><table><thead><tr><th>Задача</th><th>Проєкт</th><th>Виконавець</th><th>Статус</th><th>Пріоритет</th><th>Строк</th></tr></thead><tbody>{tasks.data.items.map(task => <tr key={task.id}><td><Link className="record-link" to={`/tasks/${task.id}`}>{task.title}</Link></td><td><Link to={`/projects/${task.project_id}`}>{task.project_name}</Link></td><td>{task.assignee_name || 'Не призначено'}</td><td><StatusBadge value={task.status} /></td><td><StatusBadge value={task.priority} /></td><td className={isOverdue(task) ? 'overdue' : ''}>{task.deadline ? new Date(task.deadline).toLocaleString('uk-UA') : 'Без строку'}</td></tr>)}{!tasks.data.items.length && <tr><td colSpan={6}>Задач за цими фільтрами немає.</td></tr>}</tbody></table></div>}<Pagination page={page} total={tasks.data.total} pageSize={20} onChange={setPage} /></>}
  </>
}

