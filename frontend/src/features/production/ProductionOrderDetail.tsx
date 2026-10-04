import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { QRCodeSVG } from 'qrcode.react'
import { Link, useParams } from 'react-router-dom'
import { api, send } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { labelForCode } from '../../lib/labels'
import type { UserOption } from '../auth/types'
import { hasCapability } from '../auth/types'
import { useSession } from '../auth/useSession'
import type { OrderProgress, ProductionItem, StageExecution, WorkItem } from './types'

export function ProductionOrderDetail() {
  const { id = '' } = useParams()
  const { data: user } = useSession()
  const canAssign = hasCapability(user, 'MANAGE_ORDERS')
  const items = useQuery({ queryKey: ['production-items', id], queryFn: ({ signal }) => api<ProductionItem[]>(`/production/orders/${id}/items`, { signal }) })
  const progress = useQuery({ queryKey: ['production-progress', id], queryFn: ({ signal }) => api<OrderProgress>(`/production/orders/${id}/progress`, { signal }) })
  const activeWork = useQuery({ queryKey: ['production-order-work', id], queryFn: ({ signal }) => api<WorkItem[]>(`/production/orders/${id}/work`, { signal }) })
  const users = useQuery({ queryKey: ['user-options'], queryFn: ({ signal }) => api<UserOption[]>('/users/options', { signal }), enabled: canAssign })
  if (items.isPending || progress.isPending || activeWork.isPending) return <Loading />
  const error = items.error || progress.error || activeWork.error || users.error
  if (error) return <ErrorNotice error={error} />
  const orderNumber = items.data?.[0]?.order_number ?? 'Виробниче замовлення'
  return <>
    <Link className="back-link" to="/production">← До виробництва</Link>
    <div className="page-heading"><div><p className="eyebrow">ВИКОНАННЯ</p><h1>{orderNumber}</h1><p className="page-description">Операції, виконавці, одиниці та партії цього замовлення.</p></div>{progress.data && <strong>{progress.data.percent}%</strong>}</div>
    {progress.data && <section><div className="section-heading"><h2>Прогрес операцій</h2><span>{progress.data.completed} / {progress.data.total}</span></div><progress max={100} value={progress.data.percent} /><div className="stage-progress-grid">{progress.data.stages.map(stage => <div key={stage.stage_code}><strong>{stage.stage_name}</strong><span>{stage.completed} / {stage.total}</span><progress max={stage.total || 1} value={stage.completed} /></div>)}</div></section>}
    <section><div className="section-heading"><h2>Активні операції</h2><span>{activeWork.data?.length ?? 0}</span></div><div className="table-scroll"><table><thead><tr><th>Виріб / партія</th><th>Етап</th><th>Статус</th><th>Виконавець</th></tr></thead><tbody>{activeWork.data?.map(row => <tr key={row.execution.id}><td><Link className="record-link" to={`/my-work/items/${row.item.id}`}>{row.item.identifier}</Link></td><td>{row.execution.stage_name}</td><td><StatusBadge value={row.execution.status} /></td><td>{canAssign ? <AssignmentSelect execution={row.execution} users={users.data ?? []} orderId={id} /> : row.execution.assigned_user_id ? 'Призначено' : 'Не призначено'}</td></tr>)}{!activeWork.data?.length && <tr><td colSpan={4}>Активних операцій немає.</td></tr>}</tbody></table></div></section>
    <section className="print-area"><div className="section-heading"><h2>Одиниці, партії та QR</h2><Button onClick={() => window.print()}>Друкувати мітки</Button></div><div className="label-grid">{items.data?.map(item => <article className="qr-label" key={item.id}><QRCodeSVG value={`${window.location.origin}/my-work/items/${item.id}`} size={112} /><div><strong>{item.identifier}</strong><span>{item.product_name} · {item.revision_code}</span><span>{item.quantity} од. · {labelForCode(item.tracking_mode)}</span></div></article>)}</div></section>
  </>
}

function AssignmentSelect({ execution, users, orderId }: { execution: StageExecution; users: UserOption[]; orderId: string }) {
  const cache = useQueryClient()
  const mutation = useMutation({ mutationFn: (assigned_user_id: string | null) => send<StageExecution>(`/production/executions/${execution.id}/assignment`, 'PATCH', { assigned_user_id }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['production-order-work', orderId] }) })
  return <select aria-label="Виконавець" className="form-input" value={execution.assigned_user_id ?? ''} onChange={event => mutation.mutate(event.target.value || null)} disabled={mutation.isPending}><option value="">Не призначено</option>{users.map(option => <option key={option.id} value={option.id}>{option.full_name}</option>)}</select>
}
