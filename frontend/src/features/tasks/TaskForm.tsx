import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { useProject, useProjectOptions, useUserOptions } from '../projects/hooks'
import { priorities, taskStatuses } from './types'
import type { Task } from './types'

const schema = z.object({ title: z.string().trim().min(1, 'Вкажіть назву задачі').max(255), description: z.string().max(20000),
  project_id: z.string().uuid('Оберіть проєкт'), branch_id: z.string(), assignee_id: z.string(), status: z.enum(taskStatuses), priority: z.enum(priorities), deadline: z.string(), result: z.string().max(20000) })
type Values = z.infer<typeof schema>

function localDate(value: string | null) {
  if (!value) return ''
  const date = new Date(value)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 16)
}

export function TaskFormPage() {
  const { id } = useParams(), { data: user } = useSession()
  const task = useQuery({ queryKey: ['task', id], enabled: Boolean(id), queryFn: ({ signal }) => api<Task>(`/tasks/${id}`, { signal }) })
  if (!hasCapability(user, 'MANAGE_TASKS')) return <ErrorNotice error={new Error('Статус і результат власної задачі можна змінити на її сторінці.')} />
  if (id && task.isPending) return <Loading />
  if (task.error) return <ErrorNotice error={task.error} />
  return <TaskForm key={id ?? 'new'} task={task.data} />
}

function TaskForm({ task }: { task?: Task }) {
  const [search] = useSearchParams(), projects = useProjectOptions(), users = useUserOptions(), navigate = useNavigate(), cache = useQueryClient()
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { title: task?.title ?? '', description: task?.description ?? '',
    project_id: task?.project_id ?? search.get('project_id') ?? '', branch_id: task?.branch_id ?? search.get('branch_id') ?? '', assignee_id: task?.assignee_id ?? '', status: task?.status ?? 'TODO', priority: task?.priority ?? 'NORMAL', deadline: localDate(task?.deadline ?? null), result: task?.result ?? '' } })
  const projectId = useWatch({ control: form.control, name: 'project_id' }), project = useProject(projectId)
  const candidates = project.data?.participants.filter(p => users.data?.some(u => u.id === p.id) || task?.assignee_id === p.id) ?? []
  const mutation = useMutation({ mutationFn: (values: Values) => send<Task>(task ? `/tasks/${task.id}` : '/tasks', task ? 'PATCH' : 'POST', {
    ...values, branch_id: values.branch_id || null, assignee_id: values.assignee_id || null, deadline: values.deadline ? new Date(values.deadline).toISOString() : null,
  }), onSuccess: async (saved) => { await cache.invalidateQueries({ queryKey: ['tasks'] }); await cache.invalidateQueries({ queryKey: ['task-summary'] }); cache.setQueryData(['task', saved.id], saved); navigate(`/tasks/${saved.id}`) } })
  return <><div className="page-heading"><h1>{task ? 'Редагувати задачу' : 'Нова задача'}</h1></div><form className="form-panel form-stack" onSubmit={form.handleSubmit(values => mutation.mutate(values))}>
    <Field label="Назва задачі" error={form.formState.errors.title?.message}><Input {...form.register('title')} /></Field>
    <div className="editor-grid"><Field label="Проєкт" error={form.formState.errors.project_id?.message}><select className="form-input" {...form.register('project_id', { onChange: () => form.setValue('assignee_id', '') })}><option value="">Оберіть проєкт</option>{projects.data?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
    <Field label="Виконавець"><select className="form-input" disabled={!project.data} {...form.register('assignee_id')}><option value="">Не призначено</option>{candidates.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select></Field></div>
    {project.data && <p className="page-description">Виконавець має бути учасником проєкту. <Link className="record-link" to={`/projects/${projectId}`}>Відкрити проєкт</Link></p>}
    {form.getValues('branch_id') && <p className="page-description">Задача належить R&D гілці. <Link className="record-link" to={`/rnd/branches/${form.getValues('branch_id')}`}>Відкрити гілку</Link></p>}
    <Field label="Опис" error={form.formState.errors.description?.message}><textarea className="form-input" {...form.register('description')} /></Field>
    <div className="editor-grid"><Field label="Статус"><select className="form-input" {...form.register('status')}>{taskStatuses.map(s => <option key={s}>{s}</option>)}</select></Field>
    <Field label="Пріоритет"><select className="form-input" {...form.register('priority')}>{priorities.map(p => <option key={p}>{p}</option>)}</select></Field></div>
    <Field label="Строк виконання (місцевий час)"><Input type="datetime-local" {...form.register('deadline')} /></Field>
    <Field label="Результат" error={form.formState.errors.result?.message}><textarea className="form-input" {...form.register('result')} /></Field>
    <ErrorNotice error={mutation.error || projects.error || project.error || users.error} /><div className="form-actions"><Button type="submit" disabled={mutation.isPending || !project.data || users.isPending || users.isError}>Зберегти задачу</Button><Button asChild variant="outline"><Link to={task ? `/tasks/${task.id}` : '/tasks'}>Скасувати</Link></Button></div>
  </form></>
}

