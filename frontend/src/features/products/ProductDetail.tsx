import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { FilesPanel } from '../collaboration/FilesPanel'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import type { BomItem, ComponentOption, Product, ProductRevision, UnitOfMeasure, WorkerPreview } from './types'
import { labelForCode } from '../../lib/labels'

const tabs = ['Огляд', 'Версії', 'Специфікація', 'Технологічна карта', 'Прошивки', 'Виробничий маршрут', 'Документи'] as const
export function ProductDetail() {
  const { id = '' } = useParams(), [tab, setTab] = useState<(typeof tabs)[number]>('Огляд'), [selected, setSelected] = useState('')
  const product = useQuery({ queryKey: ['product', id], queryFn: ({ signal }) => api<Product>(`/products/${id}`, { signal }) })
  const revisions = useQuery({ queryKey: ['product-revisions', id], queryFn: ({ signal }) => api<ProductRevision[]>(`/products/${id}/revisions`, { signal }) })
  const revisionId = selected || revisions.data?.[0]?.id || ''
  const revision = revisions.data?.find(item => item.id === revisionId)
  const { data: user } = useSession()
  const canEdit = hasCapability(user, 'MANAGE_ENGINEERING')
  if (product.isPending || revisions.isPending) return <Loading />
  if (!product.data) return <ErrorNotice error={product.error || new Error('Виріб не знайдено.')} />
  return <><Link className="back-link" to="/products">← До продукції</Link><div className="page-heading"><div><p className="eyebrow">{product.data.code} · {product.data.category_name}</p><h1>{product.data.name}</h1><p className="page-description">{product.data.description || 'Опис ще не додано.'}</p></div><StatusBadge value={product.data.lifecycle} /></div><div className="tabs">{tabs.map(value => <button key={value} className={tab === value ? 'selected' : ''} onClick={() => setTab(value)}>{value}</button>)}</div>
    {tab === 'Огляд' && <><dl className="detail-grid"><div><dt>Категорія</dt><dd>{product.data.category_name}</dd></div><div><dt>Режим обліку</dt><dd>{labelForCode(product.data.tracking_mode)}</dd></div><div><dt>Поточна версія</dt><dd>{revisions.data?.find(item => item.id === product.data.current_revision_id)?.revision_code || 'Ще не затверджена'}</dd></div></dl><FilesPanel owner={{ kind: 'product', id }} /></>}
    {tab === 'Версії' && <Revisions productId={id} rows={revisions.data ?? []} selected={revisionId} select={setSelected} />}
    {tab === 'Специфікація' && <Bom revision={revision} canEdit={canEdit} />}{tab === 'Технологічна карта' && <Technology revisionId={revisionId} />}
    {tab === 'Прошивки' && <Records revisionId={revisionId} path="/firmware/requirements" empty="Вимог до прошивки ще немає." />}{tab === 'Виробничий маршрут' && <Records revisionId={revisionId} path="/production-routes/revisions" empty="Маршрут ще не налаштовано." />}{tab === 'Документи' && revisionId && <FilesPanel owner={{ kind: 'product_revision', id: revisionId }} />}</>
}

function Revisions({ productId, rows, selected, select }: { productId: string; rows: ProductRevision[]; selected: string; select: (id: string) => void }) {
  const cache = useQueryClient(), [code, setCode] = useState('')
  const create = useMutation({ mutationFn: () => send<ProductRevision>(`/products/${productId}/revisions`, 'POST', { revision_code: code, technical_characteristics: {}, standard_cost: null, currency: 'UAH', revision_instructions: '' }), onSuccess: async item => { await cache.invalidateQueries({ queryKey: ['product-revisions', productId] }); setCode(''); select(item.id) } })
  const transition = useMutation({ mutationFn: ({ id, status }: { id: string; status: string }) => send(`/products/revisions/${id}/status`, 'POST', { status }), onSuccess: async () => cache.invalidateQueries({ queryKey: ['product-revisions', productId] }) })
  function submit(event: FormEvent) { event.preventDefault(); create.mutate() }
  return <section className="form-panel"><form className="filters" onSubmit={submit}><Input placeholder="Код нової версії" required value={code} onChange={event => setCode(event.target.value)} /><Button type="submit">Створити чернетку</Button></form><ErrorNotice error={create.error || transition.error} /><div className="table-scroll"><table><thead><tr><th>Версія</th><th>Стан</th><th>Джерело</th><th>Дії</th></tr></thead><tbody>{rows.map(item => <tr key={item.id} className={selected === item.id ? 'selected-row' : ''}><td><button className="record-link" onClick={() => select(item.id)}>{item.revision_code}</button></td><td><StatusBadge value={item.status} /></td><td>{item.source_setup_id ? 'Передано з розробки' : 'Вручну'}</td><td>{item.status === 'DRAFT' ? <Button variant="outline" onClick={() => transition.mutate({ id: item.id, status: 'IN_REVIEW' })}>На перевірку</Button> : item.status === 'IN_REVIEW' ? <Button onClick={() => transition.mutate({ id: item.id, status: 'RELEASED' })}>Затвердити</Button> : 'Незмінна'}</td></tr>)}{!rows.length && <tr><td colSpan={4}>Версій ще немає.</td></tr>}</tbody></table></div></section>
}

function Bom({ revision, canEdit }: { revision: ProductRevision | undefined; canEdit: boolean }) {
  const revisionId = revision?.id ?? '', cache = useQueryClient()
  const [componentId, setComponentId] = useState(''), [quantity, setQuantity] = useState('1')
  const [uomId, setUomId] = useState(''), [position, setPosition] = useState(''), [required, setRequired] = useState(true)
  const query = useQuery({ queryKey: ['bom', revisionId], enabled: !!revisionId, queryFn: ({ signal }) => api<BomItem[]>(`/products/revisions/${revisionId}/bom`, { signal }) })
  const components = useQuery({ queryKey: ['component-options'], queryFn: ({ signal }) => api<ComponentOption[]>('/components/options', { signal }) })
  const uoms = useQuery({ queryKey: ['uoms'], queryFn: ({ signal }) => api<UnitOfMeasure[]>('/components/uoms', { signal }) })
  const add = useMutation({ mutationFn: () => send<BomItem>(`/products/revisions/${revisionId}/bom`, 'POST', { component_id: componentId, quantity, uom_id: uomId || null, position, sequence: query.data?.length ?? 0, required, notes: '' }), onSuccess: async () => { setComponentId(''); setQuantity('1'); setUomId(''); setPosition(''); await cache.invalidateQueries({ queryKey: ['bom', revisionId] }) } })
  const remove = useMutation({ mutationFn: (itemId: string) => send<void>(`/products/revisions/${revisionId}/bom/${itemId}`, 'DELETE'), onSuccess: async () => cache.invalidateQueries({ queryKey: ['bom', revisionId] }) })
  if (!revision) return <p className="empty-state">Оберіть версію.</p>
  const editable = canEdit && revision.status === 'DRAFT'
  return <section className="form-panel"><div className="section-heading"><div><h2>Специфікація версії {revision.revision_code}</h2><p className="page-description">Склад комплектуючих фіксується після затвердження версії.</p></div><StatusBadge value={revision.status} /></div>
    {editable && <form className="bom-editor" onSubmit={event => { event.preventDefault(); add.mutate() }}><Field label="Комплектуюча"><select required className="form-input" value={componentId} onChange={event => setComponentId(event.target.value)}><option value="">Оберіть компонент</option>{components.data?.map(item => <option key={item.id} value={item.id}>{item.name}{item.sku ? ` · ${item.sku}` : ''}</option>)}</select></Field><Field label="Кількість"><Input required type="number" min="0.0001" step="0.0001" value={quantity} onChange={event => setQuantity(event.target.value)} /></Field><Field label="Одиниця"><select className="form-input" value={uomId} onChange={event => setUomId(event.target.value)}><option value="">За замовчуванням компонента</option>{uoms.data?.map(item => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></Field><Field label="Позиція"><Input placeholder="Напр. M1, FC, корпус" value={position} onChange={event => setPosition(event.target.value)} /></Field><label className="bom-required"><input type="checkbox" checked={required} onChange={event => setRequired(event.target.checked)} /> Обов’язкова позиція</label><Button type="submit" disabled={add.isPending || !componentId}>Додати до специфікації</Button></form>}
    {!editable && <p className="immutable-notice">{revision.status === 'DRAFT' ? 'У вас немає прав редагувати специфікацію.' : 'Ця версія незмінна. Для змін створіть нову чернетку версії.'}</p>}
    <ErrorNotice error={query.error || components.error || uoms.error || add.error || remove.error} />{query.isPending ? <Loading /> : <div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Кількість</th><th>Од.</th><th>Позиція</th><th>Обов’язковий</th>{editable && <th>Дії</th>}</tr></thead><tbody>{query.data?.map(item => <tr key={item.id}><td>{components.data?.find(component => component.id === item.component_id)?.name ?? 'Компонент недоступний'}</td><td>{item.quantity}</td><td>{uoms.data?.find(uom => uom.id === item.uom_id)?.code ?? '—'}</td><td>{item.position || '—'}</td><td><input type="checkbox" checked={item.required} readOnly /></td>{editable && <td><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm('Видалити цю комплектуючу зі специфікації?')) remove.mutate(item.id) }}>Видалити</Button></td>}</tr>)}{!query.data?.length && <tr><td colSpan={editable ? 6 : 5}>Специфікація цієї версії порожня.</td></tr>}</tbody></table></div>}</section>
}
function Technology({ revisionId }: { revisionId: string }) { const query = useQuery({ queryKey: ['technology', revisionId], enabled: !!revisionId, retry: false, queryFn: ({ signal }) => api<WorkerPreview>(`/technology/revisions/${revisionId}/preview`, { signal }) }); return <section className="worker-preview"><p className="eyebrow">ПЕРЕГЛЯД ДЛЯ ПРАЦІВНИКА</p>{query.error && <p className="empty-state">Технологічну карту ще не створено.</p>}{query.data?.operations.map(op => <article className="operation-card" key={op.id}><span className="phase-badge">КРОК {op.sequence + 1}</span><h3>{op.name}</h3>{op.blocks.map(block => <div className={`content-block block-${block.block_type.toLowerCase()}`} key={block.id}>{String(block.payload.text ?? block.block_type)}</div>)}{op.checklist_items.map(item => <label className="checklist-row" key={item.id}><input type="checkbox" disabled />{item.text}{item.required && ' *'}</label>)}</article>)}</section> }
function Records({ revisionId, path, empty }: { revisionId: string; path: string; empty: string }) { const query = useQuery({ queryKey: [path, revisionId], enabled: !!revisionId, queryFn: ({ signal }) => api<Array<Record<string, unknown>>>(`${path}/${revisionId}`, { signal }) }); if (query.isPending) return <Loading />; return <section className="form-panel"><ErrorNotice error={query.error} /><p>{query.data?.length ? `${query.data.length} записів` : empty}</p></section> }
