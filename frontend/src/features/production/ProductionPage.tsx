import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { labelForCode } from '../../lib/labels'
import type { ComponentOption, Customer, Order, ProcurementRecord, ProcurementStatus, Supplier } from './types'

const procurementTransitions: Record<ProcurementStatus, ProcurementStatus[]> = {
  REQUIRED: ['RFQ', 'ORDERED', 'ISSUE'], RFQ: ['ORDERED', 'ISSUE'], ORDERED: ['PAID', 'IN_TRANSIT', 'ISSUE'],
  PAID: ['IN_TRANSIT', 'ISSUE'], IN_TRANSIT: ['CUSTOMS', 'RECEIVED', 'ISSUE'], CUSTOMS: ['RECEIVED', 'ISSUE'],
  RECEIVED: [], ISSUE: ['RFQ', 'ORDERED', 'PAID', 'IN_TRANSIT', 'CUSTOMS', 'RECEIVED'],
}

export function ProductionPage() {
  const isOrdersPage = useLocation().pathname.startsWith('/orders')
  const [showOrder, setShowOrder] = useState(false), [showCustomer, setShowCustomer] = useState(false)
  const orders = useQuery({ queryKey: ['orders'], queryFn: ({ signal }) => api<Page<Order>>('/orders?page_size=100', { signal }) })
  const customers = useQuery({ queryKey: ['customers'], queryFn: ({ signal }) => api<Customer[]>('/orders/customers', { signal }) })
  return <>
    <div className="page-heading"><div><p className="eyebrow">{isOrdersPage ? 'ПЛАНУВАННЯ' : 'ВИКОНАННЯ'}</p><h1>{isOrdersPage ? 'Замовлення' : 'Виробництво'}</h1><p className="page-description">{isOrdersPage ? 'Замовники, замовлення, потреба в матеріалах і закупівлі.' : 'Черга виконання замовлень, виробничі операції та фактичний прогрес.'}</p></div><div className="form-actions"><Button onClick={() => setShowCustomer(v => !v)}>Новий замовник</Button><Button onClick={() => setShowOrder(v => !v)}>Нове замовлення</Button></div></div>
    {showCustomer && <CustomerForm onDone={() => setShowCustomer(false)} />}
    {showOrder && customers.data && <OrderForm customers={customers.data} onDone={() => setShowOrder(false)} />}
    <ErrorNotice error={orders.error || customers.error} />{orders.isPending && <Loading />}
    {orders.data && <div className="table-scroll"><table><thead><tr><th>Замовлення</th><th>Замовник</th><th>Отримувач</th><th>Дата</th><th>Строк</th><th>Статус</th></tr></thead><tbody>{orders.data.items.map(order => <tr key={order.id}><td><Link className="record-link" to={`/orders/${order.id}`}>{order.order_number}</Link></td><td>{order.customer_name}</td><td>{order.recipient || '—'}</td><td>{order.order_date}</td><td>{order.deadline ?? '—'}</td><td><StatusBadge value={order.status} /></td></tr>)}{!orders.data.items.length && <tr><td colSpan={6}>Замовлень ще немає.</td></tr>}</tbody></table></div>}
    <ProcurementPanel />
  </>
}

function ProcurementPanel() {
  const cache = useQueryClient(), [show, setShow] = useState(false), [component, setComponent] = useState(''), [supplier, setSupplier] = useState(''), [quantity, setQuantity] = useState('1'), [status, setStatus] = useState('REQUIRED')
  const records = useQuery({ queryKey: ['procurement'], queryFn: ({ signal }) => api<Page<ProcurementRecord>>('/procurement?page_size=100', { signal }) })
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: ({ signal }) => api<Supplier[]>('/procurement/suppliers', { signal }) })
  const components = useQuery({ queryKey: ['component-options'], queryFn: ({ signal }) => api<ComponentOption[]>('/components/options', { signal }) })
  const mutation = useMutation({ mutationFn: () => send<ProcurementRecord>('/procurement', 'POST', { component_id: component, supplier_id: supplier || null, quantity, unit_price: null, currency: 'UAH', order_date: null, expected_date: null, tracking_number: '', status, notes: '' }), onSuccess: async () => { setShow(false); await cache.invalidateQueries({ queryKey: ['procurement'] }) } })
  const changeStatus = useMutation({ mutationFn: ({ id, status: next }: { id: string; status: ProcurementStatus }) => send<ProcurementRecord>(`/procurement/${id}/status`, 'POST', { status: next }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['procurement'] }) })
  return <section><div className="section-heading"><h2>Закупівлі</h2><Button onClick={() => setShow(v => !v)}>Нова закупівля</Button></div>{show && <form className="form-panel editor-grid" onSubmit={e => { e.preventDefault(); mutation.mutate() }}><Field label="Компонент"><select required className="form-input" value={component} onChange={e => setComponent(e.target.value)}><option value="">Оберіть компонент</option>{components.data?.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="Постачальник"><select className="form-input" value={supplier} onChange={e => setSupplier(e.target.value)}><option value="">Не вказано</option>{suppliers.data?.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="Кількість"><Input type="number" min="0.0001" step="0.0001" value={quantity} onChange={e => setQuantity(e.target.value)} /></Field><Field label="Статус"><select className="form-input" value={status} onChange={e => setStatus(e.target.value)}><option value="REQUIRED">Потреба</option><option value="RFQ">Запит ціни</option><option value="ORDERED">Замовлено</option><option value="PAID">Оплачено</option><option value="IN_TRANSIT">В дорозі</option><option value="CUSTOMS">Митниця</option><option value="RECEIVED">Отримано</option><option value="ISSUE">Проблема</option></select></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>Створити закупівлю</Button></form>}<ErrorNotice error={records.error || suppliers.error || components.error || changeStatus.error} />{records.data && <div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Постачальник</th><th>Кількість</th><th>Статус</th><th>Наступний крок</th><th>Очікується</th></tr></thead><tbody>{records.data.items.map(row => <tr key={row.id}><td>{row.component_name}</td><td>{row.supplier_name ?? '—'}</td><td>{row.quantity}</td><td><StatusBadge value={row.status} /></td><td>{procurementTransitions[row.status].length ? <select aria-label={`Статус закупівлі ${row.component_name}`} className="form-input compact-select" value="" disabled={changeStatus.isPending} onChange={event => { if (event.target.value) changeStatus.mutate({ id: row.id, status: event.target.value as ProcurementStatus }) }}><option value="">Змінити статус…</option>{procurementTransitions[row.status].map(next => <option key={next} value={next}>{labelForCode(next)}</option>)}</select> : <span className="muted-text">Завершено</span>}</td><td>{row.expected_date ?? '—'}</td></tr>)}{!records.data.items.length && <tr><td colSpan={6}>Закупівель ще немає.</td></tr>}</tbody></table></div>}</section>
}

function CustomerForm({ onDone }: { onDone: () => void }) {
  const cache = useQueryClient(), [name, setName] = useState(''), [contact, setContact] = useState('')
  const mutation = useMutation({ mutationFn: () => send<Customer>('/orders/customers', 'POST', { name, contact_details: contact, notes: '' }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['customers'] }); onDone() } })
  return <form className="form-panel editor-grid" onSubmit={e => { e.preventDefault(); mutation.mutate() }}><Field label="Назва замовника"><Input required value={name} onChange={e => setName(e.target.value)} /></Field><Field label="Контакти"><Input value={contact} onChange={e => setContact(e.target.value)} /></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending}>Створити замовника</Button></form>
}

function OrderForm({ customers, onDone }: { customers: Customer[]; onDone: () => void }) {
  const cache = useQueryClient(), today = new Date().toISOString().slice(0, 10)
  const [number, setNumber] = useState(''), [customer, setCustomer] = useState(customers[0]?.id ?? ''), [recipient, setRecipient] = useState(''), [deadline, setDeadline] = useState('')
  const mutation = useMutation({ mutationFn: () => send<Order>('/orders', 'POST', { order_number: number, customer_id: customer, recipient, destination: '', order_date: today, deadline: deadline || null, notes: '' }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['orders'] }); onDone() } })
  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate() }
  return <form className="form-panel form-stack" onSubmit={submit}><h2>Нове замовлення</h2><div className="editor-grid"><Field label="Номер"><Input required value={number} onChange={e => setNumber(e.target.value)} /></Field><Field label="Замовник"><select required className="form-input" value={customer} onChange={e => setCustomer(e.target.value)}>{customers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Отримувач"><Input value={recipient} onChange={e => setRecipient(e.target.value)} /></Field><Field label="Дедлайн"><Input type="date" value={deadline} onChange={e => setDeadline(e.target.value)} /></Field></div><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending || !customers.length}>Створити</Button></form>
}
