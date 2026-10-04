import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'
import { send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { useProject, useUserOptions } from './hooks'
import { labelForCode } from '../../lib/labels'
import { projectStatuses } from './types'
import type { Project } from './types'

const schema = z.object({ name: z.string().trim().min(1, 'Вкажіть назву').max(255), description: z.string().max(20000), goal: z.string().max(20000),
  start_date: z.string(), deadline: z.string(), status: z.enum(projectStatuses), responsible_user_id: z.string().uuid('Оберіть відповідального'), participant_ids: z.array(z.string().uuid()) }).refine(values => !values.start_date || !values.deadline || values.deadline >= values.start_date, { message: 'Дедлайн не може бути раніше дати початку', path: ['deadline'] })
type Values = z.infer<typeof schema>

export function ProjectFormPage() {
  const { id } = useParams(), { data: user } = useSession(), project = useProject(id ?? '')
  if (!hasCapability(user, 'MANAGE_PROJECTS')) return <ErrorNotice error={new Error('Недостатньо прав для редагування проєктів.')} />
  if (id && project.isPending) return <Loading />
  if (project.error) return <ErrorNotice error={project.error} />
  return <ProjectForm key={id ?? 'new'} project={project.data} />
}

function ProjectForm({ project }: { project?: Project }) {
  const users = useUserOptions(), navigate = useNavigate(), cache = useQueryClient(), { data: me } = useSession()
  const form = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { name: project?.name ?? '', description: project?.description ?? '',
    goal: project?.goal ?? '', start_date: project?.start_date ?? '', deadline: project?.deadline ?? '', status: project?.status ?? 'PLANNED', responsible_user_id: project?.responsible_user_id ?? me?.id ?? '', participant_ids: project?.participants.map(user => user.id) ?? [] } })
  const mutation = useMutation({ mutationFn: (values: Values) => send<Project>(project ? `/projects/${project.id}` : '/projects', project ? 'PUT' : 'POST', { ...values, start_date: values.start_date || null, deadline: values.deadline || null }),
    onSuccess: async (saved) => { await cache.invalidateQueries({ queryKey: ['projects'] }); await cache.invalidateQueries({ queryKey: ['project-options'] }); cache.setQueryData(['project', saved.id], saved); navigate(`/projects/${saved.id}`) } })
  const options = [...(users.data ?? [])]
  for (const person of project?.participants ?? []) if (!options.some(item => item.id === person.id)) options.push(person)
  return <><div className="page-heading"><h1>{project ? 'Редагувати проєкт' : 'Новий проєкт'}</h1></div><form className="form-panel form-stack" onSubmit={form.handleSubmit(values => mutation.mutate(values))}>
    <Field label="Назва" error={form.formState.errors.name?.message}><Input {...form.register('name')} /></Field>
    <div className="editor-grid"><Field label="Статус"><select className="form-input" {...form.register('status')}>{projectStatuses.map(s => <option key={s} value={s}>{labelForCode(s)}</option>)}</select></Field>
    <Field label="Відповідальний" error={form.formState.errors.responsible_user_id?.message}><select className="form-input" {...form.register('responsible_user_id')}><option value="">Оберіть відповідального</option>{options.map(u => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select></Field></div>
    <Field label="Опис" error={form.formState.errors.description?.message}><textarea className="form-input" {...form.register('description')} /></Field>
    <Field label="Мета" error={form.formState.errors.goal?.message}><textarea className="form-input" {...form.register('goal')} /></Field>
    <div className="editor-grid"><Field label="Дата початку"><Input type="date" {...form.register('start_date')} /></Field><Field label="Дедлайн" error={form.formState.errors.deadline?.message}><Input type="date" {...form.register('deadline')} /></Field></div>
    <fieldset className="participants"><legend>Учасники проєкту</legend><p className="page-description">Відповідальний додається автоматично. Задачі можна призначати учасникам.</p>{options.map(u => <label key={u.id}><input type="checkbox" value={u.id} {...form.register('participant_ids')} /> {u.full_name}</label>)}</fieldset>
    <ErrorNotice error={mutation.error || users.error} /><div className="form-actions"><Button type="submit" disabled={mutation.isPending || users.isPending || users.isError}>Зберегти проєкт</Button><Button asChild variant="outline"><Link to={project ? `/projects/${project.id}` : '/projects'}>Скасувати</Link></Button></div>
  </form></>
}

