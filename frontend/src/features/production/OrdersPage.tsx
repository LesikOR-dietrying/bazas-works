import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { labelForCode } from '../../lib/labels'
import { hasCapability } from '../auth/types'
import { useSession } from '../auth/useSession'
import type { ComponentOption, Customer, Order, OrderStatus, ProcurementRecord, ProcurementStatus, Supplier } from './types'

const orderStatuses: OrderStatus[] = ['DRAFT', 'CONFIRMED', 'MATERIALS', 'PRODUCTION', 'READY', 'PARTIALLY_SHIPPED', 'SHIPPED', 'CANCELLED']
const procurementStatuses: ProcurementStatus[] = ['REQUIRED', 'RFQ', 'ORDERED', 'PAID', 'IN_TRANSIT', 'CUSTOMS', 'RECEIVED', 'ISSUE']
const procurementTransitions: Record<ProcurementStatus, ProcurementStatus[]> = {
  REQUIRED: ['RFQ', 'ORDERED', 'ISSUE'], RFQ: ['ORDERED', 'ISSUE'], ORDERED: ['PAID', 'IN_TRANSIT', 'ISSUE'],
  PAID: ['IN_TRANSIT', 'ISSUE'], IN_TRANSIT: ['CUSTOMS', 'RECEIVED', 'ISSUE'], CUSTOMS: ['RECEIVED', 'ISSUE'],
  RECEIVED: [], ISSUE: ['RFQ', 'ORDERED', 'PAID', 'IN_TRANSIT', 'CUSTOMS', 'RECEIVED'],
}

export function OrdersPage() {
  const [showOrder, setShowOrder] = useState(false), [showCustomer, setShowCustomer] = useState(false)
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [page, setPage] = useState(1)
  const params = new URLSearchParams({ q, page: String(page), page_size: '20' })
  if (status) params.set('status', status)
  const orders = useQuery({ queryKey: ['orders', params.toString()], queryFn: ({ signal }) => api<Page<Order>>(`/orders?${params}`, { signal }) })
  const customers = useQuery({ queryKey: ['customers'], queryFn: ({ signal }) => api<Customer[]>('/orders/customers', { signal }) })
  const { data: user } = useSession(), canManage = hasCapability(user, 'MANAGE_ORDERS'), canProcure = hasCapability(user, 'MANAGE_PROCUREMENT')
  return <>
    <div className="page-heading"><div><p className="eyebrow">ПЛАНУВАННЯ</p><h1>Замовлення</h1><p className="page-description">Замовники, замовлення, потреба в матеріалах і закупівлі.</p></div>{canManage && <div className="form-actions"><Button onClick={() => setShowCustomer(value => !value)}>Новий замовник</Button><Button onClick={() => setShowOrder(value => !value)}>Нове замовлення</Button></div>}</div>
    {showCustomer && <CustomerForm onDone={() => setShowCustomer(false)} />}
    {showOrder && customers.data && <OrderForm customers={customers.data} onDone={() => setShowOrder(false)} />}
    <CustomerList customers={customers.data ?? []} loading={customers.isPending} error={customers.error} />
    <OrdersTable orders={orders.data} loading={orders.isPending} error={orders.error} q={q} status={status} page={page} onQuery={value => { setQ(value); setPage(1) }} onStatus={value => { setStatus(value); setPage(1) }} onPage={setPage} />
    <ProcurementPanel canManage={canProcure} />
  </>
}

function CustomerList({ customers, loading, error }: { customers: Customer[]; loading: boolean; error: Error | null }) {
  return <section><div className="section-heading"><div><h2>Замовники</h2><p className="page-description">Довідник замовників для нових замовлень.</p></div><span>{customers.length}</span></div><ErrorNotice error={error} />{loading ? <Loading /> : <div className="table-scroll"><table><thead><tr><th>Назва</th><th>Контакти</th><th>Примітки</th></tr></thead><tbody>{customers.map(customer => <tr key={customer.id}><td>{customer.name}</td><td>{customer.contact_details || '—'}</td><td>{customer.notes || '—'}</td></tr>)}{!customers.length && <tr><td colSpan={3}>Замовників ще немає.</td></tr>}</tbody></table></div>}</section>
}

function OrdersTable({ orders, loading, error, q, status, page, onQuery, onStatus, onPage }: { orders: Page<Order> | undefined; loading: boolean; error: Error | null; q: string; status: string; page: number; onQuery: (value: string) => void; onStatus: (value: string) => void; onPage: (value: number) => void }) {
  const today = new Date().toISOString().slice(0, 10)
  return <section><div className="section-heading"><div><h2>План замовлень</h2><p className="page-description">Пошук і сторінки завантажуються з API.</p></div></div><div className="filters"><Input aria-label="Пошук замовлень" placeholder="Номер або отримувач" value={q} onChange={event => onQuery(event.target.value)} /><select aria-label="Статус замовлення" className="form-input" value={status} onChange={event => onStatus(event.target.value)}><option value="">Усі статуси</option>{orderStatuses.map(value => <option key={value} value={value}>{labelForCode(value)}</option>)}</select></div><ErrorNotice error={error} />{loading && <Loading />}{orders && <><div className="table-scroll"><table><thead><tr><th>Номер</th><th>Дата</th><th>Замовник</th><th>Вироби / комплектації</th><th>Кількість</th><th>Строк</th><th>Матеріали</th><th>Виробництво</th><th>Відвантаження</th></tr></thead><tbody>{orders.items.map(order => { const overdue = Boolean(order.deadline && order.deadline < today && !['READY', 'SHIPPED', 'CANCELLED'].includes(order.status)); return <tr key={order.id}><td><Link className="record-link" to={`/orders/${order.id}`}>{order.order_number}</Link></td><td>{order.order_date}</td><td>{order.customer_name}</td><td>{order.product_summary || 'Позицій ще немає'}</td><td>{order.total_quantity}</td><td>{order.deadline ?? '—'}{overdue && <small className="field-error"> Прострочено</small>}</td><td>{order.status === 'DRAFT' ? 'Специфікація не зафіксована' : 'Розраховано'}</td><td><StatusBadge value={order.status} /></td><td>Облік ще не реалізований</td></tr> })}{!orders.items.length && <tr><td colSpan={9}>Замовлень не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={orders.total} pageSize={orders.page_size} onChange={onPage} /></>}</section>
}

function ProcurementPanel({ canManage }: { canManage: boolean }) {
  const cache = useQueryClient(), [show, setShow] = useState(false), [component, setComponent] = useState(''), [supplier, setSupplier] = useState(''), [quantity, setQuantity] = useState('1'), [newStatus, setNewStatus] = useState<ProcurementStatus>('REQUIRED')
  const [q, setQ] = useState(''), [status, setStatus] = useState(''), [page, setPage] = useState(1)
  const params = new URLSearchParams({ q, page: String(page), page_size: '20' })
  if (status) params.set('status', status)
  const records = useQuery({ queryKey: ['procurement', params.toString()], queryFn: ({ signal }) => api<Page<ProcurementRecord>>(`/procurement?${params}`, { signal }) })
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: ({ signal }) => api<Supplier[]>('/procurement/suppliers', { signal }) })
  const components = useQuery({ queryKey: ['component-options'], queryFn: ({ signal }) => api<ComponentOption[]>('/components/options', { signal }) })
  const mutation = useMutation({ mutationFn: () => send<ProcurementRecord>('/procurement', 'POST', { component_id: component, supplier_id: supplier || null, quantity, unit_price: null, currency: 'UAH', order_date: null, expected_date: null, tracking_number: '', status: newStatus, notes: '' }), onSuccess: async () => { setShow(false); await cache.invalidateQueries({ queryKey: ['procurement'] }) } })
  const changeStatus = useMutation({ mutationFn: ({ id, status: next }: { id: string; status: ProcurementStatus }) => send<ProcurementRecord>(`/procurement/${id}/status`, 'POST', { status: next }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['procurement'] }) })
  return <section><div className="section-heading"><div><h2>Закупівлі</h2><p className="page-description">Постачання компонентів для потреб замовлень.</p></div>{canManage && <Button onClick={() => setShow(value => !value)}>Нова закупівля</Button>}</div>{show && canManage && <form className="form-panel editor-grid" onSubmit={event => { event.preventDefault(); mutation.mutate() }}><Field label="Компонент"><select required className="form-input" value={component} onChange={event => setComponent(event.target.value)}><option value="">Оберіть компонент</option>{components.data?.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="Постачальник"><select className="form-input" value={supplier} onChange={event => setSupplier(event.target.value)}><option value="">Не вказано</option>{suppliers.data?.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="Кількість"><Input type="number" min="0.0001" step="0.0001" value={quantity} onChange={event => setQuantity(event.target.value)} /></Field><Field label="Статус"><select className="form-input" value={newStatus} onChange={event => setNewStatus(event.target.value as ProcurementStatus)}>{procurementStatuses.map(value => <option key={value} value={value}>{labelForCode(value)}</option>)}</select></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>Створити закупівлю</Button></form>}<div className="filters"><Input aria-label="Пошук закупівель" placeholder="Компонент, постачальник або номер відстеження" value={q} onChange={event => { setQ(event.target.value); setPage(1) }} /><select aria-label="Статус закупівлі" className="form-input" value={status} onChange={event => { setStatus(event.target.value); setPage(1) }}><option value="">Усі статуси</option>{procurementStatuses.map(value => <option key={value} value={value}>{labelForCode(value)}</option>)}</select></div><ErrorNotice error={records.error || suppliers.error || components.error || changeStatus.error} />{records.isPending && <Loading />}{records.data && <><div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Постачальник</th><th>Кількість</th><th>Статус</th><th>Наступний крок</th><th>Очікується</th></tr></thead><tbody>{records.data.items.map(row => <tr key={row.id}><td>{row.component_name}</td><td>{row.supplier_name ?? '—'}</td><td>{row.quantity}</td><td><StatusBadge value={row.status} /></td><td>{canManage && procurementTransitions[row.status].length ? <select aria-label={`Статус закупівлі ${row.component_name}`} className="form-input compact-select" value="" disabled={changeStatus.isPending} onChange={event => { if (event.target.value) changeStatus.mutate({ id: row.id, status: event.target.value as ProcurementStatus }) }}><option value="">Змінити статус…</option>{procurementTransitions[row.status].map(next => <option key={next} value={next}>{labelForCode(next)}</option>)}</select> : <span className="muted-text">{procurementTransitions[row.status].length ? 'Лише перегляд' : 'Завершено'}</span>}</td><td>{row.expected_date ?? '—'}</td></tr>)}{!records.data.items.length && <tr><td colSpan={6}>Закупівель не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={records.data.total} pageSize={records.data.page_size} onChange={setPage} /></>}</section>
}

function CustomerForm({ onDone }: { onDone: () => void }) {
  const cache = useQueryClient(), [name, setName] = useState(''), [contact, setContact] = useState('')
  const mutation = useMutation({ mutationFn: () => send<Customer>('/orders/customers', 'POST', { name, contact_details: contact, notes: '' }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['customers'] }); onDone() } })
  return <form className="form-panel editor-grid" onSubmit={event => { event.preventDefault(); mutation.mutate() }}><Field label="Назва замовника"><Input required value={name} onChange={event => setName(event.target.value)} /></Field><Field label="Контакти"><Input value={contact} onChange={event => setContact(event.target.value)} /></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>Створити замовника</Button></form>
}

function OrderForm({ customers, onDone }: { customers: Customer[]; onDone: () => void }) {
  const cache = useQueryClient(), today = new Date().toISOString().slice(0, 10)
  const [number, setNumber] = useState(''), [customer, setCustomer] = useState(customers[0]?.id ?? ''), [recipient, setRecipient] = useState(''), [deadline, setDeadline] = useState('')
  const mutation = useMutation({ mutationFn: () => send<Order>('/orders', 'POST', { order_number: number, customer_id: customer, recipient, destination: '', order_date: today, deadline: deadline || null, notes: '' }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['orders'] }); onDone() } })
  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate() }
  return <form className="form-panel form-stack" onSubmit={submit}><h2>Нове замовлення</h2><div className="editor-grid"><Field label="Номер"><Input required value={number} onChange={event => setNumber(event.target.value)} /></Field><Field label="Замовник"><select required className="form-input" value={customer} onChange={event => setCustomer(event.target.value)}>{customers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Отримувач"><Input value={recipient} onChange={event => setRecipient(event.target.value)} /></Field><Field label="Строк"><Input type="date" value={deadline} onChange={event => setDeadline(event.target.value)} /></Field></div><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending || !customers.length}>Створити</Button></form>
}
