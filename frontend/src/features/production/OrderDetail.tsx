import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import type { BomItem, ComponentOption, Deviation, MaterialSummary, Order, OrderItem, OrderProgress, OrderVariant, Requirement, RevisionOption } from './types'

export function OrderDetail() {
  const { id = '' } = useParams(), cache = useQueryClient()
  const order = useQuery({ queryKey: ['order', id], queryFn: ({ signal }) => api<Order>(`/orders/${id}`, { signal }) })
  const items = useQuery({ queryKey: ['order-items', id], queryFn: ({ signal }) => api<OrderItem[]>(`/orders/${id}/items`, { signal }) })
  const revisions = useQuery({ queryKey: ['released-revisions'], queryFn: ({ signal }) => api<RevisionOption[]>('/orders/revision-options', { signal }) })
  const requirements = useQuery({ queryKey: ['requirements', id], queryFn: ({ signal }) => api<Requirement[]>(`/orders/${id}/requirements`, { signal }) })
  const materials = useQuery({ queryKey: ['materials', id], queryFn: ({ signal }) => api<MaterialSummary[]>(`/orders/${id}/materials`, { signal }) })
  const progress = useQuery({ queryKey: ['production-progress', id], queryFn: ({ signal }) => api<OrderProgress>(`/production/orders/${id}/progress`, { signal }), enabled: order.data?.status === 'PRODUCTION' || order.data?.status === 'READY' })
  const transition = useMutation({ mutationFn: (status: string) => send<Order>(`/orders/${id}/status`, 'POST', { status }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['order', id] }) })
  const launch = useMutation({ mutationFn: () => send<{ created_items: number }>(`/production/orders/${id}/launch`, 'POST'), onSuccess: async () => { await Promise.all([cache.invalidateQueries({ queryKey: ['order', id] }), cache.invalidateQueries({ queryKey: ['production-items', id] }), cache.invalidateQueries({ queryKey: ['production-progress', id] })]) } })
  if (order.isPending || items.isPending) return <Loading />
  if (!order.data) return <ErrorNotice error={order.error} />
  const totalRequired = materials.data?.reduce((sum, row) => sum + Number(row.required), 0) ?? 0
  const totalCovered = materials.data?.reduce((sum, row) => sum + Number(row.required) - Number(row.missing), 0) ?? 0
  return <><Link className="back-link" to="/orders">← До замовлень</Link><div className="page-heading"><div><p className="eyebrow">ЗАМОВЛЕННЯ</p><h1>{order.data.order_number}</h1><p className="page-description">{order.data.customer_name} · {order.data.recipient || 'отримувача не вказано'}</p></div><StatusBadge value={order.data.status} /></div>
    <div className="form-actions">{order.data.status === 'DRAFT' && <Button onClick={() => transition.mutate('CONFIRMED')}>Підтвердити замовлення</Button>}{order.data.status === 'CONFIRMED' && <Button onClick={() => transition.mutate('MATERIALS')}>Передати в матеріали</Button>}{order.data.status === 'MATERIALS' && <Button onClick={() => launch.mutate()} disabled={launch.isPending}>Запустити виробництво</Button>}</div><ErrorNotice error={transition.error || launch.error || items.error || revisions.error} />
    {order.data.status === 'DRAFT' && revisions.data && <AddItem orderId={id} revisions={revisions.data} />}
    <section><div className="section-heading"><h2>Позиції та варіанти</h2><span>{items.data?.length ?? 0}</span></div>{items.data?.map(item => <ItemCard key={item.id} item={item} orderId={id} />)}{!items.data?.length && <div className="empty-state"><p>Додайте першу позицію з затвердженої версії продукції.</p></div>}</section>
    <section><div className="section-heading"><h2>Забезпечення матеріалами</h2><span>{Math.round(totalCovered)} / {Math.round(totalRequired)}</span></div><div className="progress-block"><progress max={totalRequired || 1} value={totalCovered} /><span>Покрито {totalRequired ? Math.round(totalCovered / totalRequired * 100) : 0}% потреби</span></div>{materials.data && <div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Потрібно</th><th>Замовлено</th><th>В дорозі</th><th>Не вистачає</th></tr></thead><tbody>{materials.data.map(row => <tr key={row.component_id}><td>{requirements.data?.find(req => req.component_id === row.component_id)?.component_name ?? 'Компонент'}</td><td>{row.required}</td><td>{row.ordered}</td><td>{row.in_transit}</td><td>{row.missing}</td></tr>)}</tbody></table></div>}</section>
    {progress.data && <section><div className="section-heading"><h2>Стан виробництва</h2><span>{progress.data.percent}%</span></div><div className="progress-block"><progress max={100} value={progress.data.percent} /><span>{progress.data.completed} з {progress.data.total} операцій виконано</span></div><Link className="record-link" to={`/production/orders/${id}/execution`}>Відкрити у виробництві →</Link></section>}
  </>
}

function AddItem({ orderId, revisions }: { orderId: string; revisions: RevisionOption[] }) {
  const cache = useQueryClient(), [revision, setRevision] = useState(revisions[0]?.id ?? ''), [quantity, setQuantity] = useState(1)
  const mutation = useMutation({ mutationFn: () => send<OrderItem>(`/orders/${orderId}/items`, 'POST', { product_revision_id: revision, quantity, required_date: null, notes: '' }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['order-items', orderId] }) })
  return <form className="form-panel editor-grid" onSubmit={e => { e.preventDefault(); mutation.mutate() }}><Field label="Продукція і версія"><select className="form-input" required value={revision} onChange={e => setRevision(e.target.value)}>{revisions.map(row => <option key={row.id} value={row.id}>{row.product_name} · {row.revision_code}</option>)}</select></Field><Field label="Кількість"><Input type="number" min={1} value={quantity} onChange={e => setQuantity(Number(e.target.value))} /></Field><ErrorNotice error={mutation.error} /><Button type="submit" disabled={mutation.isPending || !revision}>Додати позицію</Button></form>
}

function ItemCard({ item, orderId }: { item: OrderItem; orderId: string }) {
  const cache = useQueryClient(), [name, setName] = useState(''), [quantity, setQuantity] = useState(1)
  const variants = useQuery({ queryKey: ['variants', item.id], queryFn: ({ signal }) => api<OrderVariant[]>(`/orders/items/${item.id}/variants`, { signal }) })
  const split = useMutation({ mutationFn: () => send<OrderVariant>(`/orders/items/${item.id}/variants`, 'POST', { name, quantity, notes: '' }), onSuccess: async () => { setName(''); await cache.invalidateQueries({ queryKey: ['variants', item.id] }) } })
  const release = useMutation({ mutationFn: () => send<OrderVariant[]>(`/orders/items/${item.id}/release-variants`, 'POST'), onSuccess: async () => { await Promise.all([cache.invalidateQueries({ queryKey: ['variants', item.id] }), cache.invalidateQueries({ queryKey: ['requirements', orderId] }), cache.invalidateQueries({ queryKey: ['materials', orderId] })]) } })
  return <article className="operation-card"><div className="view-controls"><div><h3>{item.product_name} · {item.revision_code}</h3><p>{item.quantity} од.</p></div><Button onClick={() => release.mutate()} disabled={release.isPending}>Випустити варіанти</Button></div><ErrorNotice error={variants.error || split.error || release.error} />
    <form className="filters" onSubmit={e => { e.preventDefault(); split.mutate() }}><Input required placeholder="Назва нового варіанта" value={name} onChange={e => setName(e.target.value)} /><Input type="number" min={1} max={item.quantity - 1} value={quantity} onChange={e => setQuantity(Number(e.target.value))} /><Button type="submit" disabled={split.isPending}>Розділити</Button></form>
    {variants.data?.map(variant => <VariantRow key={variant.id} variant={variant} revisionId={item.product_revision_id} itemId={item.id} />)}
  </article>
}

function VariantRow({ variant, revisionId, itemId }: { variant: OrderVariant; revisionId: string; itemId: string }) {
  const cache = useQueryClient(), [show, setShow] = useState(false), [bomId, setBomId] = useState(''), [componentId, setComponentId] = useState(''), [reason, setReason] = useState(''), [quantity, setQuantity] = useState('1')
  const bom = useQuery({ queryKey: ['bom', revisionId], queryFn: ({ signal }) => api<BomItem[]>(`/products/revisions/${revisionId}/bom`, { signal }), enabled: show })
  const components = useQuery({ queryKey: ['component-options'], queryFn: ({ signal }) => api<ComponentOption[]>('/components/options', { signal }), enabled: show })
  const deviations = useQuery({ queryKey: ['deviations', variant.id], queryFn: ({ signal }) => api<Deviation[]>(`/orders/variants/${variant.id}/deviations`, { signal }) })
  const add = useMutation({ mutationFn: () => send<Deviation>(`/orders/variants/${variant.id}/deviations`, 'POST', { original_bom_item_id: bomId, replacement_component_id: componentId, quantity_per_product: quantity, reason, required_retest: false, test_ids: [], notes: '' }), onSuccess: async () => { setShow(false); await Promise.all([cache.invalidateQueries({ queryKey: ['deviations', variant.id] }), cache.invalidateQueries({ queryKey: ['variants', itemId] })]) } })
  const decide = useMutation({ mutationFn: ({ id, action }: { id: string; action: 'approve' | 'reject' }) => send<Deviation>(`/orders/deviations/${id}/${action}`, 'POST'), onSuccess: async () => { await Promise.all([cache.invalidateQueries({ queryKey: ['deviations', variant.id] }), cache.invalidateQueries({ queryKey: ['variants', itemId] })]) } })
  return <div className="variant-row"><div><strong>{variant.name}</strong> · {variant.quantity} од. <StatusBadge value={variant.status} /></div>{!variant.is_standard && variant.status === 'DRAFT' && <Button onClick={() => setShow(v => !v)}>Запросити заміну</Button>}{show && <form className="form-panel form-stack" onSubmit={e => { e.preventDefault(); add.mutate() }}><Field label="Позиція специфікації"><select required className="form-input" value={bomId} onChange={e => setBomId(e.target.value)}><option value="">Оберіть позицію</option>{bom.data?.map(row => <option key={row.id} value={row.id}>{row.position || 'BOM'} · {row.quantity}</option>)}</select></Field><Field label="Компонент заміни"><select required className="form-input" value={componentId} onChange={e => setComponentId(e.target.value)}><option value="">Оберіть компонент</option>{components.data?.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}</select></Field><Field label="Кількість на виріб"><Input type="number" min="0.0001" step="0.0001" value={quantity} onChange={e => setQuantity(e.target.value)} /></Field><Field label="Причина"><Input required value={reason} onChange={e => setReason(e.target.value)} /></Field><ErrorNotice error={add.error} /><Button type="submit" disabled={add.isPending}>Надіслати на погодження</Button></form>}{deviations.data?.map(row => <div className="activity-row" key={row.id}><span>{row.reason} · {row.quantity_per_product} на виріб</span>{!row.approved_at && variant.status === 'PENDING_APPROVAL' && <span className="form-actions"><Button onClick={() => decide.mutate({ id: row.id, action: 'approve' })}>Погодити</Button><Button onClick={() => decide.mutate({ id: row.id, action: 'reject' })}>Відхилити</Button></span>}</div>)}</div>
}
