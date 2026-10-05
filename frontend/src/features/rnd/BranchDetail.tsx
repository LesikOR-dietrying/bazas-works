import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { TasksPage } from '../tasks/TasksPage'
import { TestsPage } from '../tests/TestsPage'
import { FilesPanel } from '../collaboration/FilesPanel'
import { CommentsPanel } from '../collaboration/CommentsPanel'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import type { SetupOption } from '../engineering/types'
import type { Product, ProductRevision, ProductVariant } from '../products/types'
import type { BranchConfiguration, BranchFirmware, BranchStatus, ConfigurationComparison, ConfigurationRole, PromotionRequest, RndBranch } from './types'

const tabs = ['Огляд', 'Конфігурації', 'Задачі', 'Випробування', 'Прошивки', 'Файли', 'Коментарі', 'Передавання в продукцію'] as const
type Tab = typeof tabs[number]
function valueText(value: unknown) { return value === null || value === undefined || value === '' ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value) }

export function BranchDetail() {
  const { id = '' } = useParams(), { data: user } = useSession(), cache = useQueryClient(), [tab, setTab] = useState<Tab>('Огляд')
  const branch = useQuery({ queryKey: ['rnd-branch', id], queryFn: ({ signal }) => api<RndBranch>(`/rnd/branches/${id}`, { signal }) })
  const transition = useMutation({ mutationFn: (status: BranchStatus) => send<RndBranch>(`/rnd/branches/${id}/transition`, 'POST', { status, result_summary: branch.data?.result_summary ?? '' }), onSuccess: async saved => { cache.setQueryData(['rnd-branch', id], saved); await cache.invalidateQueries({ queryKey: ['rnd-branches', saved.project_id] }) } })
  if (branch.isPending) return <Loading />
  if (!branch.data) return <ErrorNotice error={branch.error} />
  const data = branch.data, canEdit = hasCapability(user, 'MANAGE_ENGINEERING'), canReview = hasCapability(user, 'MANAGE_PROJECTS')
  const available: BranchStatus[] = data.status === 'OPEN' ? ['IN_REVIEW', 'CLOSED'] : data.status === 'IN_REVIEW' ? ['OPEN', 'CLOSED'] : data.status === 'REJECTED' ? ['OPEN', 'CLOSED'] : data.status === 'APPROVED' ? ['CLOSED'] : []
  const next = available
  return <><div className="page-heading"><div><Link className="back-link" to={`/projects/${data.project_id}`}>← Проєкт</Link><p className="eyebrow">R&D ГІЛКА</p><h1>{data.name}</h1></div><StatusBadge value={data.status} /></div>
    <ErrorNotice error={transition.error} /><div className="form-actions">{canEdit && data.status !== 'CLOSED' && <Button onClick={() => setTab('Передавання в продукцію')}>Передати в продукцію</Button>}{canEdit && next.map(status => <Button key={status} variant="outline" disabled={transition.isPending} onClick={() => transition.mutate(status)}>{status}</Button>)}</div>
    <div className="tabs" role="tablist" aria-label="Розділи R&D гілки">{tabs.map(item => <button key={item} role="tab" aria-selected={tab === item} className={tab === item ? 'selected' : ''} onClick={() => setTab(item)}>{item}</button>)}</div>
    {tab === 'Огляд' ? <BranchOverview branch={data} canEdit={canEdit} />
      : tab === 'Конфігурації' ? <Configurations branch={data} canEdit={canEdit} />
      : tab === 'Задачі' ? <TasksPage projectId={data.project_id} branchId={data.id} />
      : tab === 'Випробування' ? <TestsPage projectId={data.project_id} branchId={data.id} />
      : tab === 'Прошивки' ? <Firmware branchId={data.id} />
      : tab === 'Файли' ? <FilesPanel owner={{ kind: 'branch', id: data.id }} />
      : tab === 'Коментарі' ? <CommentsPanel owner={{ kind: 'branch', id: data.id }} />
      : <Promotions branch={data} canEdit={canEdit} canReview={canReview} />}
  </>
}

function BranchOverview({ branch, canEdit }: { branch: RndBranch; canEdit: boolean }) {
  const cache = useQueryClient(), [editing, setEditing] = useState(false), [name, setName] = useState(branch.name)
  const [purpose, setPurpose] = useState(branch.purpose), [changeSummary, setChangeSummary] = useState(branch.change_summary), [resultSummary, setResultSummary] = useState(branch.result_summary)
  const save = useMutation({ mutationFn: () => send<RndBranch>(`/rnd/branches/${branch.id}`, 'PUT', { name: name.trim(), parent_id: branch.parent_id, responsible_user_id: branch.responsible_user_id, purpose, change_summary: changeSummary, result_summary: resultSummary }), onSuccess: async saved => { cache.setQueryData(['rnd-branch', branch.id], saved); await cache.invalidateQueries({ queryKey: ['rnd-branches', branch.project_id] }); setEditing(false) } })
  if (editing) return <section className="form-panel"><form className="form-stack" onSubmit={(event: FormEvent) => { event.preventDefault(); if (name.trim()) save.mutate() }}><Field label="Назва"><input className="form-input" required value={name} onChange={event => setName(event.target.value)} /></Field><Field label="Мета"><textarea className="form-input" value={purpose} onChange={event => setPurpose(event.target.value)} /></Field><Field label="Опис змін"><textarea className="form-input" value={changeSummary} onChange={event => setChangeSummary(event.target.value)} /></Field><Field label="Підсумок результату"><textarea className="form-input" value={resultSummary} onChange={event => setResultSummary(event.target.value)} /></Field><ErrorNotice error={save.error} /><div className="form-actions"><Button type="submit" disabled={save.isPending}>Зберегти</Button><Button type="button" variant="outline" onClick={() => setEditing(false)}>Скасувати</Button></div></form></section>
  return <section className="form-panel"><div className="page-heading"><h2>Мета й результат</h2>{canEdit && (branch.status === 'OPEN' || branch.status === 'REJECTED') && <Button variant="outline" onClick={() => setEditing(true)}>Редагувати</Button>}</div><dl className="detail-grid"><div><dt>Відповідальний</dt><dd>{branch.responsible_name}</dd></div><div><dt>Батьківська гілка</dt><dd>{branch.parent_name || 'Головна'}</dd></div><div><dt>Мета</dt><dd>{branch.purpose || 'Не вказано'}</dd></div><div><dt>Зміни</dt><dd>{branch.change_summary || 'Не описано'}</dd></div><div><dt>Результат</dt><dd>{branch.result_summary || 'Ще не зафіксовано'}</dd></div></dl></section>
}

function Configurations({ branch, canEdit }: { branch: RndBranch; canEdit: boolean }) {
  const cache = useQueryClient(), [setupId, setSetupId] = useState(''), [role, setRole] = useState<ConfigurationRole>('CANDIDATE'), [candidateId, setCandidateId] = useState('')
  const links = useQuery({ queryKey: ['rnd-configurations', branch.id], queryFn: ({ signal }) => api<BranchConfiguration[]>(`/rnd/branches/${branch.id}/configurations`, { signal }) })
  const setups = useQuery({ queryKey: ['project-setups', branch.project_id], queryFn: ({ signal }) => api<SetupOption[]>(`/projects/${branch.project_id}/setups`, { signal }) })
  const comparison = useQuery({ queryKey: ['rnd-comparison', branch.id, candidateId], enabled: Boolean(candidateId), queryFn: ({ signal }) => api<ConfigurationComparison>(`/rnd/branches/${branch.id}/comparison?candidate_setup_id=${candidateId}`, { signal }) })
  const refresh = () => cache.invalidateQueries({ queryKey: ['rnd-configurations', branch.id] })
  const add = useMutation({ mutationFn: () => send<BranchConfiguration>(`/rnd/branches/${branch.id}/configurations`, 'POST', { setup_id: setupId, role }), onSuccess: async () => { await refresh(); setSetupId('') } })
  const remove = useMutation({ mutationFn: (id: string) => send(`/rnd/branches/${branch.id}/configurations/${id}`, 'DELETE'), onSuccess: refresh })
  const available = setups.data?.filter(setup => !links.data?.some(link => link.setup_id === setup.id)) ?? []
  const candidates = links.data?.filter(link => link.role === 'CANDIDATE') ?? []
  const mutable = branch.status === 'OPEN' || branch.status === 'REJECTED'
  return <><section className="form-panel"><h2>Експериментальні конфігурації</h2>{canEdit && mutable && <form className="form-actions" onSubmit={(event: FormEvent) => { event.preventDefault(); if (setupId) add.mutate() }}><select aria-label="Конфігурація" className="form-input" required value={setupId} onChange={event => setSetupId(event.target.value)}><option value="">Оберіть конфігурацію</option>{available.map(setup => <option key={setup.id} value={setup.id}>{setup.name} · {setup.version}</option>)}</select><select aria-label="Роль конфігурації" className="form-input" value={role} onChange={event => setRole(event.target.value as ConfigurationRole)}><option value="BASELINE">Базова</option><option value="CANDIDATE">Кандидат</option></select><Button type="submit" disabled={!setupId || add.isPending}>Додати</Button></form>}
    <ErrorNotice error={links.error || setups.error || add.error || remove.error} />{links.isPending && <Loading />}{links.data && <div className="table-scroll"><table><thead><tr><th>Роль</th><th>Конфігурація</th><th>Статус</th><th>Дії</th></tr></thead><tbody>{links.data.map(link => <tr key={link.id}><td><StatusBadge value={link.role} /></td><td><Link className="record-link" to={`/setups/${link.setup_id}`}>{link.setup.name} · {link.setup.version}</Link></td><td><StatusBadge value={link.setup.status} /></td><td>{canEdit && mutable && <Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm('Від’єднати конфігурацію від гілки?')) remove.mutate(link.id) }}>Від’єднати</Button>}</td></tr>)}{!links.data.length && <tr><td colSpan={4}>Конфігурації ще не додані.</td></tr>}</tbody></table></div>}</section>
    <section className="form-panel"><h2>Порівняння з базовою конфігурацією</h2><Field label="Конфігурація-кандидат"><select className="form-input" value={candidateId} onChange={event => setCandidateId(event.target.value)}><option value="">Оберіть кандидата</option>{candidates.map(link => <option key={link.id} value={link.setup_id}>{link.setup.name} · {link.setup.version}</option>)}</select></Field><ErrorNotice error={comparison.error} />{comparison.isFetching && <Loading />}{comparison.data && <><h3>Параметри</h3><div className="table-scroll"><table><thead><tr><th>Поле</th><th>Базова</th><th>Кандидат</th></tr></thead><tbody>{comparison.data.attribute_changes.map(change => <tr key={change.field}><td>{change.field}</td><td>{valueText(change.baseline)}</td><td>{valueText(change.candidate)}</td></tr>)}{!comparison.data.attribute_changes.length && <tr><td colSpan={3}>Відмінностей немає.</td></tr>}</tbody></table></div><h3>Специфікація</h3><div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Позиція</th><th>Базова</th><th>Кандидат</th></tr></thead><tbody>{comparison.data.bom_changes.map(change => <tr key={`${change.component_id}-${change.position}`}><td>{change.component_name}</td><td>{change.position || '—'}</td><td>{change.baseline_quantity}</td><td>{change.candidate_quantity}</td></tr>)}{!comparison.data.bom_changes.length && <tr><td colSpan={4}>Специфікація не відрізняється.</td></tr>}</tbody></table></div></>}</section></>
}

function Firmware({ branchId }: { branchId: string }) {
  const firmware = useQuery({ queryKey: ['rnd-firmware', branchId], queryFn: ({ signal }) => api<BranchFirmware[]>(`/rnd/branches/${branchId}/firmware`, { signal }) })
  return <section className="form-panel"><h2>Прошивки конфігурацій гілки</h2><ErrorNotice error={firmware.error} />{firmware.isPending && <Loading />}{firmware.data && <div className="table-scroll"><table><thead><tr><th>Ревізія</th><th>Тип</th><th>Версія</th><th>Конфігурація</th><th>Дата</th></tr></thead><tbody>{firmware.data.map(item => <tr key={item.id}><td>{item.version_name}</td><td>{item.firmware_type}</td><td>{item.firmware_version}</td><td><Link className="record-link" to={`/setups/${item.setup_id}`}>Відкрити</Link></td><td>{new Date(item.created_at).toLocaleString('uk-UA')}</td></tr>)}{!firmware.data.length && <tr><td colSpan={5}>Прошивок ще немає.</td></tr>}</tbody></table></div>}</section>
}

function Promotions({ branch, canEdit, canReview }: { branch: RndBranch; canEdit: boolean; canReview: boolean }) {
  const cache = useQueryClient(), navigate = useNavigate(), [candidateId, setCandidateId] = useState(''), [reason, setReason] = useState(''), [notes, setNotes] = useState('')
  const [promotionId, setPromotionId] = useState(''), [productId, setProductId] = useState(''), [variantId, setVariantId] = useState(''), [revisionCode, setRevisionCode] = useState('')
  const requests = useQuery({ queryKey: ['rnd-promotions', branch.id], queryFn: ({ signal }) => api<PromotionRequest[]>(`/rnd/branches/${branch.id}/promotion-requests`, { signal }) })
  const configs = useQuery({ queryKey: ['rnd-configurations', branch.id], queryFn: ({ signal }) => api<BranchConfiguration[]>(`/rnd/branches/${branch.id}/configurations`, { signal }) })
  const invalidate = async () => { await cache.invalidateQueries({ queryKey: ['rnd-promotions', branch.id] }); await cache.invalidateQueries({ queryKey: ['rnd-branch', branch.id] }) }
  const create = useMutation({ mutationFn: () => send<PromotionRequest>(`/rnd/branches/${branch.id}/promotion-requests`, 'POST', { candidate_setup_id: candidateId, reason: reason.trim() }), onSuccess: async () => { await invalidate(); setReason('') } })
  const review = useMutation({ mutationFn: ({ id, status }: { id: string; status: 'APPROVED' | 'REJECTED' }) => send<PromotionRequest>(`/rnd/promotion-requests/${id}/review`, 'POST', { status, review_notes: notes }), onSuccess: invalidate })
  const reopen = useMutation({ mutationFn: () => send<RndBranch>(`/rnd/branches/${branch.id}/transition`, 'POST', { status: 'OPEN', result_summary: branch.result_summary }), onSuccess: async saved => { cache.setQueryData(['rnd-branch', branch.id], saved); await cache.invalidateQueries({ queryKey: ['rnd-branches', branch.project_id] }) } })
  const products = useQuery({ queryKey: ['products-for-promotion'], enabled: Boolean(promotionId), queryFn: ({ signal }) => api<Page<Product>>('/products?page=1&page_size=100', { signal }) })
  const variants = useQuery({ queryKey: ['product-variants', productId], enabled: Boolean(productId), queryFn: ({ signal }) => api<ProductVariant[]>(`/products/${productId}/variants`, { signal }) })
  const revisions = useQuery({ queryKey: ['product-revisions', productId], enabled: Boolean(productId), queryFn: ({ signal }) => api<ProductRevision[]>(`/products/${productId}/revisions`, { signal }) })
  const promote = useMutation({ mutationFn: () => send<ProductRevision>(`/products/${productId}/promote`, 'POST', { promotion_request_id: promotionId, revision_code: revisionCode.trim(), variant_id: variantId || null }), onSuccess: revision => { void cache.invalidateQueries({ queryKey: ['product-revisions', productId] }); const params = new URLSearchParams({ variant: revision.variant_id, revision: revision.id, tab: 'specification' }); navigate(`/products/${revision.product_id}?${params}`) } })
  const chooseProduct = (value: string) => { setProductId(value); setVariantId(''); setRevisionCode('') }
  const suggestCode = (value: string) => {
    setVariantId(value)
    const count = revisions.data?.filter(item => item.variant_id === value).length ?? 0
    setRevisionCode(`V${count + 1}`)
  }
  const candidates = configs.data?.filter(item => item.role === 'CANDIDATE') ?? []
  return <section className="form-panel"><h2>Передавання в продукцію</h2><p className="page-description">Спочатку погодьте конфігурацію-кандидата. Після погодження оберіть модель і комплектацію — система створить у ній нову чернетку версії зі специфікацією та посиланням на результат розробки.</p>{canEdit && branch.status === 'OPEN' && <form className="form-stack" onSubmit={(event: FormEvent) => { event.preventDefault(); if (candidateId && reason.trim()) create.mutate() }}><Field label="Конфігурація-кандидат"><select className="form-input" required value={candidateId} onChange={event => setCandidateId(event.target.value)}><option value="">Оберіть</option>{candidates.map(item => <option key={item.id} value={item.setup_id}>{item.setup.name} · {item.setup.version}</option>)}</select></Field><Field label="Обґрунтування"><textarea className="form-input" required value={reason} onChange={event => setReason(event.target.value)} /></Field><Button type="submit" disabled={create.isPending || !candidateId || !reason.trim()}>Надіслати на розгляд</Button></form>}
    {canReview && <Field label="Примітка рецензента"><textarea className="form-input" value={notes} onChange={event => setNotes(event.target.value)} /></Field>}<ErrorNotice error={requests.error || configs.error || create.error || review.error || reopen.error || products.error || variants.error || revisions.error || promote.error} />{requests.isPending && <Loading />}{requests.data?.map(item => <article className="comment-card" key={item.id}><div className="comment-header"><strong>{item.candidate_name}</strong><StatusBadge value={item.status} /><span>{item.requested_by_name}</span><time>{new Date(item.created_at).toLocaleString('uk-UA')}</time></div><p>{item.reason}</p>{item.review_notes && <p className="page-description">Рішення: {item.review_notes}</p>}{canReview && item.status === 'REQUESTED' && <div className="form-actions"><Button disabled={review.isPending} onClick={() => review.mutate({ id: item.id, status: 'APPROVED' })}>Погодити</Button><Button variant="destructive" disabled={review.isPending} onClick={() => review.mutate({ id: item.id, status: 'REJECTED' })}>Відхилити</Button></div>}{canEdit && item.status === 'APPROVED' && promotionId !== item.id && <Button variant="outline" onClick={() => { setPromotionId(item.id); setProductId(''); setVariantId(''); setRevisionCode('') }}>Створити чернетку продукції</Button>}{promotionId === item.id && <form className="form-stack" onSubmit={event => { event.preventDefault(); if (productId && variantId && revisionCode.trim()) promote.mutate() }}><Field label="Модель виробу"><select className="form-input" required value={productId} onChange={event => chooseProduct(event.target.value)}><option value="">Оберіть модель</option>{products.data?.items.map(product => <option key={product.id} value={product.id}>{product.code} · {product.name}</option>)}</select></Field><Field label="Комплектація"><select className="form-input" required value={variantId} onChange={event => suggestCode(event.target.value)}><option value="">Оберіть комплектацію</option>{variants.data?.map(variant => <option key={variant.id} value={variant.id}>{variant.code} · {variant.name}</option>)}</select></Field><Field label="Код нової версії"><Input required placeholder="Наприклад V2" value={revisionCode} onChange={event => setRevisionCode(event.target.value)} /><small>Це коротка назва версії всередині комплектації. Код моделі вже заданий у каталозі продукції.</small></Field><div className="form-actions"><Button type="submit" disabled={promote.isPending || !productId || !variantId || !revisionCode.trim()}>Передати в продукцію</Button><Button type="button" variant="outline" onClick={() => setPromotionId('')}>Скасувати</Button></div></form>}</article>)}{requests.data && !requests.data.length && <div className="empty-state"><p>Запитів на передавання ще немає.</p>{branch.status === 'APPROVED' && canEdit && <><p>Цю гілку було схвалено старим способом без запиту. Поверніть її до підготовки, потім оберіть кандидата й надішліть запит.</p><Button variant="outline" disabled={reopen.isPending} onClick={() => reopen.mutate()}>Повернути до підготовки передавання</Button></>}</div>}
  </section>
}
