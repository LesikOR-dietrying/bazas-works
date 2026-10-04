import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { send } from '../../api/client'
import { ErrorNotice } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { taskStatuses, isOverdue } from './types'
import type { Task, TaskStatus } from './types'
import { labelForCode } from '../../lib/labels'

export function TaskBoard({ tasks }: { tasks: Task[] }) {
  const cache = useQueryClient()
  const change = useMutation({ mutationFn: ({ id, status }: { id: string; status: TaskStatus }) => send(`/tasks/${id}`, 'PATCH', { status }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['tasks'] }); await cache.invalidateQueries({ queryKey: ['task-summary'] }); await cache.invalidateQueries({ queryKey: ['task'] }) } })
  return <><ErrorNotice error={change.error} /><p className="page-description">Дошка показує поточну сторінку результатів. Змінюйте статус у картці.</p><div className="kanban">{taskStatuses.map(status => <section key={status} className="kanban-column"><h2>{labelForCode(status)} <span>{tasks.filter(t => t.status === status).length}</span></h2>
    {tasks.filter(t => t.status === status).map(task => <article className="task-card" key={task.id}><Link className="record-link" to={`/tasks/${task.id}`}>{task.title}</Link><p>{task.project_name}</p><StatusBadge value={task.priority} /><p>{task.assignee_name || 'Без виконавця'}</p>{task.deadline && <p className={isOverdue(task) ? 'overdue' : ''}>{new Date(task.deadline).toLocaleString('uk-UA')}</p>}
      <select className="form-input" aria-label={`Статус: ${task.title}`} value={task.status} disabled={change.isPending} onChange={e => change.mutate({ id: task.id, status: e.target.value as TaskStatus })}>{taskStatuses.map(s => <option key={s} value={s}>{labelForCode(s)}</option>)}</select></article>)}</section>)}</div></>
}
