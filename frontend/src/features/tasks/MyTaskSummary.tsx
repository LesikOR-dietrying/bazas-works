import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import type { TaskSummary } from './types'

export function MyTaskSummary() {
  const summary = useQuery({ queryKey: ['task-summary', 'mine'], queryFn: ({ signal }) => api<TaskSummary>('/tasks/summary?mine=true', { signal }) })
  if (summary.isPending) return <Loading />
  if (!summary.data) return <ErrorNotice error={summary.error} />
  return <section aria-label="Мої задачі" className="summary-grid">{[
    ['Активні задачі', summary.data.active], ['Прострочені', summary.data.overdue], ['Заблоковані', summary.data.blocked], ['Завершені за 7 днів', summary.data.completed_recently],
  ].map(([label, count]) => <Link key={label} to="/tasks" className="summary-card"><span>{label}</span><strong>{count}</strong></Link>)}</section>
}
