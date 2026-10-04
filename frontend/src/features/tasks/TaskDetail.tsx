import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { taskStatuses, isOverdue } from './types'
import type { Task } from './types'
import { FilesPanel } from '../collaboration/FilesPanel'
import { CommentsPanel } from '../collaboration/CommentsPanel'
import { labelForCode } from '../../lib/labels'

export function TaskDetail() {
  const { id = '' } = useParams(), { data: user } = useSession(), cache = useQueryClient(), navigate = useNavigate()
  const task = useQuery({ queryKey: ['task', id], queryFn: ({ signal }) => api<Task>(`/tasks/${id}`, { signal }) })
  const remove = useMutation({ mutationFn: () => send(`/tasks/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['tasks'] }); await cache.invalidateQueries({ queryKey: ['task-summary'] }); navigate('/tasks') } })
  if (task.isPending) return <Loading />
  if (!task.data) return <ErrorNotice error={task.error} />
  const data = task.data, editor = hasCapability(user, 'MANAGE_TASKS')
  return <><div className="page-heading"><div><Link className="back-link" to="/tasks">← Задачі</Link><h1>{data.title}</h1></div><div className="form-actions"><StatusBadge value={data.status} />{editor && <><Button asChild variant="outline"><Link to={`/tasks/${id}/edit`}>Редагувати</Link></Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити задачу «${data.title}»? Цю дію неможливо скасувати.`)) remove.mutate() }}>Видалити</Button></>}</div></div>
    <ErrorNotice error={remove.error} /><section className="form-panel"><dl className="detail-grid"><div><dt>Проєкт</dt><dd><Link className="record-link" to={`/projects/${data.project_id}`}>{data.project_name}</Link></dd></div><div><dt>Виконавець</dt><dd>{data.assignee_name || 'Не призначено'}</dd></div><div><dt>Пріоритет</dt><dd><StatusBadge value={data.priority} /></dd></div><div><dt>Строк</dt><dd className={isOverdue(data) ? 'overdue' : ''}>{data.deadline ? new Date(data.deadline).toLocaleString('uk-UA') : 'Без строку'}</dd></div><div><dt>Створив</dt><dd>{data.created_by_name}</dd></div></dl>
    <h2>Опис</h2><p className="description-text">{data.description || 'Опис ще не додано.'}</p></section>
    <TaskResult key={`${data.id}-${data.updated_at}`} task={data} />
    <FilesPanel owner={{ kind: 'task', id }} /><CommentsPanel owner={{ kind: 'task', id }} />
  </>
}

const schema = z.object({ status: z.enum(taskStatuses), result: z.string().max(20000, 'Максимум 20 000 символів') })
function TaskResult({ task }: { task: Task }) {
  const cache = useQueryClient(), form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema), defaultValues: { status: task.status, result: task.result } })
  const mutation = useMutation({ mutationFn: (values: z.infer<typeof schema>) => send<Task>(`/tasks/${task.id}`, 'PATCH', values), onSuccess: async (saved) => { cache.setQueryData(['task', task.id], saved); await cache.invalidateQueries({ queryKey: ['tasks'] }); await cache.invalidateQueries({ queryKey: ['task-summary'] }) } })
  return <form className="form-panel form-stack" onSubmit={form.handleSubmit(values => mutation.mutate(values))}><h2>Статус і результат</h2><Field label="Статус задачі"><select className="form-input" {...form.register('status')}>{taskStatuses.map(s => <option key={s} value={s}>{labelForCode(s)}</option>)}</select></Field><Field label="Результат виконання" error={form.formState.errors.result?.message}><textarea className="form-input" {...form.register('result')} /></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>Зберегти результат</Button></form>
}

