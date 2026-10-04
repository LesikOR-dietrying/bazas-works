import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { TasksPage } from '../tasks/TasksPage'
import { ProjectSetups } from '../engineering/ProjectSetups'
import { TestsPage } from '../tests/TestsPage'
import { FilesPanel } from '../collaboration/FilesPanel'
import { CommentsPanel } from '../collaboration/CommentsPanel'
import type { Task, TaskSummary } from '../tasks/types'
import { useProject } from './hooks'
import { BranchesPanel } from '../rnd/BranchesPanel'

const tabs = ['Overview', 'Branches', 'Tasks', 'Setups', 'Tests', 'Files', 'Comments'] as const
export function ProjectDetail() {
  const { id = '' } = useParams(), project = useProject(id), { data: user } = useSession()
  const [tab, setTab] = useState<typeof tabs[number]>('Overview'), cache = useQueryClient(), navigate = useNavigate()
  const summary = useQuery({ queryKey: ['task-summary', id], enabled: Boolean(project.data), queryFn: ({ signal }) => api<TaskSummary>(`/tasks/summary?project_id=${id}&mine=false`, { signal }) })
  const activity = useQuery({ queryKey: ['tasks', 'recent', id], enabled: Boolean(project.data), queryFn: ({ signal }) => api<Page<Task>>(`/tasks?project_id=${id}&page_size=5&sort=updated_at&direction=desc`, { signal }) })
  const remove = useMutation({ mutationFn: () => send(`/projects/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['projects'] }); await cache.invalidateQueries({ queryKey: ['project-options'] }); navigate('/projects') } })
  if (project.isPending) return <Loading />
  if (!project.data) return <ErrorNotice error={project.error} />
  const data = project.data, canEdit = hasCapability(user, 'MANAGE_PROJECTS')
  return <><div className="page-heading"><div><Link to="/projects" className="back-link">← Проєкти</Link><h1>{data.name}</h1></div><div className="form-actions"><StatusBadge value={data.status} />{canEdit && <><Button asChild variant="outline"><Link to={`/projects/${id}/edit`}>Редагувати</Link></Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити проєкт «${data.name}»? Цю дію неможливо скасувати.`)) remove.mutate() }}>Видалити</Button></>}</div></div>
    <ErrorNotice error={remove.error} /><div className="tabs" role="tablist" aria-label="Розділи проєкту">{tabs.map(t => <button key={t} role="tab" aria-selected={tab === t} className={tab === t ? 'selected' : ''} onClick={() => setTab(t)}>{t}</button>)}</div>
    {tab === 'Overview' ? <><section className="form-panel"><h2>Про проєкт</h2><p className="description-text">{data.description || 'Опис ще не додано.'}</p><dl className="detail-grid"><div><dt>Мета</dt><dd>{data.goal || 'Не вказано'}</dd></div><div><dt>Період</dt><dd>{data.start_date || '—'} — {data.deadline || '—'}</dd></div><div><dt>Відповідальний</dt><dd>{data.responsible_name}</dd></div><div><dt>Учасники</dt><dd>{data.participants.map(p => p.full_name).join(', ')}</dd></div></dl>
      <ErrorNotice error={summary.error} />{summary.data && <div className="progress-block"><label htmlFor="project-progress">Завершено {summary.data.completed} із {summary.data.total} доступних задач</label><progress id="project-progress" max={summary.data.total || 1} value={summary.data.completed} /></div>}</section>
      <section className="form-panel"><h2>Останні зміни задач</h2><ErrorNotice error={activity.error} />{activity.data?.items.map(task => <div className="activity-row" key={task.id}><Link className="record-link" to={`/tasks/${task.id}`}>{task.title}</Link><StatusBadge value={task.status} /><span>{new Date(task.updated_at).toLocaleString('uk-UA')}</span></div>)}{activity.data?.total === 0 && <p>У проєкті ще немає доступних вам задач.</p>}</section></>
      : tab === 'Branches' ? <BranchesPanel projectId={id} participants={data.participants} /> : tab === 'Tasks' ? <TasksPage projectId={id} /> : tab === 'Setups' ? <ProjectSetups projectId={id} /> : tab === 'Tests' ? <TestsPage projectId={id} /> : tab === 'Files' ? <FilesPanel owner={{ kind: 'project', id }} /> : <CommentsPanel owner={{ kind: 'project', id }} />}
  </>
}

