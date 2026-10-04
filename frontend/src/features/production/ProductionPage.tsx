import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { StatusBadge } from '../../components/StatusBadge'
import { Input } from '../../components/ui/input'
import { hasCapability } from '../auth/types'
import { useSession } from '../auth/useSession'
import type { ProductionQueueOrder } from './types'

export function ProductionPage() {
  const { data: user } = useSession()
  const canOpenOrders = hasCapability(user, 'MANAGE_ORDERS') || hasCapability(user, 'MANAGE_PROCUREMENT')
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [page, setPage] = useState(1)
  const params = new URLSearchParams({ q, page: String(page), page_size: '20' })
  if (status) params.set('status', status)
  const queue = useQuery({ queryKey: ['production-queue', params.toString()], queryFn: ({ signal }) => api<Page<ProductionQueueOrder>>(`/production/queue?${params}`, { signal }) })
  return <>
    <div className="page-heading"><div><p className="eyebrow">ВИКОНАННЯ</p><h1>Виробництво</h1><p className="page-description">Активні замовлення, операції, відповідальні та фактичний прогрес.</p></div><Link className="record-link" to="/my-work">Відкрити мою роботу →</Link></div>
    <div className="filters"><Input aria-label="Пошук виробництва" placeholder="Номер замовлення, замовник або отримувач" value={q} onChange={event => { setQ(event.target.value); setPage(1) }} /><select aria-label="Стан виробництва" className="form-input" value={status} onChange={event => { setStatus(event.target.value); setPage(1) }}><option value="">Активні та готові</option><option value="PRODUCTION">У виробництві</option><option value="READY">Готові</option></select></div>
    <ErrorNotice error={queue.error} />{queue.isPending && <Loading />}{queue.data && <><div className="table-scroll"><table className="production-queue-table"><thead><tr><th>Замовлення</th><th>Замовник</th><th>Строк</th><th>Прогрес операцій</th><th>Активні</th><th>Заблоковані</th><th>Відповідальні</th><th>Поточний виріб</th><th>Стан</th></tr></thead><tbody>{queue.data.items.map(row => <QueueRow key={row.order_id} row={row} canOpenOrders={canOpenOrders} />)}{!queue.data.items.length && <tr><td colSpan={9}>Активного виробництва не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={queue.data.total} pageSize={queue.data.page_size} onChange={setPage} /></>}
  </>
}

function QueueRow({ row, canOpenOrders }: { row: ProductionQueueOrder; canOpenOrders: boolean }) {
  return <tr><td>{canOpenOrders ? <Link className="record-link" to={`/orders/${row.order_id}`}>{row.order_number}</Link> : <strong>{row.order_number}</strong>}</td><td>{row.customer_name}</td><td>{row.deadline ?? '—'}</td><td><div className="table-progress"><span>{row.completed_quantity} / {row.planned_quantity} · {row.percent}%</span><progress max={row.planned_quantity || 1} value={row.completed_quantity} /></div></td><td>{row.active_operations}</td><td>{row.blocked_operations || '—'}</td><td>{row.assignees.length ? row.assignees.join(', ') : 'Не призначено'}</td><td>{row.current_item_id ? <Link className="record-link" to={`/my-work/items/${row.current_item_id}`}>{row.current_item_identifier}</Link> : '—'}</td><td><StatusBadge value={row.status} /></td></tr>
}
