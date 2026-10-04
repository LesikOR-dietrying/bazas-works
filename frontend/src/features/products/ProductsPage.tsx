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
import type { Product, ProductCategory, TrackingMode } from './types'

export function ProductsPage() {
  const [q, setQ] = useState(''), [category, setCategory] = useState(''), [tracking, setTracking] = useState(''), [page, setPage] = useState(1), [creating, setCreating] = useState(false)
  const params = new URLSearchParams({ q, page: String(page) }); if (category) params.set('category_id', category); if (tracking) params.set('tracking_mode', tracking)
  const products = useQuery({ queryKey: ['products', params.toString()], queryFn: ({ signal }) => api<Page<Product>>(`/products?${params}`, { signal }) })
  const categories = useQuery({ queryKey: ['product-categories'], queryFn: ({ signal }) => api<ProductCategory[]>('/products/categories', { signal }) })
  return <><div className="page-heading"><div><p className="eyebrow">КАТАЛОГ ВИРОБІВ</p><h1>Products</h1><p className="page-description">Моделі продуктів, керовані ревізії, BOM та виробничі інструкції.</p></div><Button onClick={() => setCreating(value => !value)}>{creating ? 'Закрити' : 'Новий продукт'}</Button></div>
    {creating && categories.data && <ProductCreate categories={categories.data} onDone={() => setCreating(false)} />}
    <div className="filters"><Input aria-label="Пошук продуктів" placeholder="Код або назва" value={q} onChange={event => { setQ(event.target.value); setPage(1) }} /><select className="form-input" aria-label="Категорія продукту" value={category} onChange={event => { setCategory(event.target.value); setPage(1) }}><option value="">Усі категорії</option>{categories.data?.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select className="form-input" aria-label="Режим обліку" value={tracking} onChange={event => { setTracking(event.target.value); setPage(1) }}><option value="">Усі режими</option><option value="SERIAL">Серійний</option><option value="BATCH">Партіями</option><option value="QUANTITY">Кількісний</option></select></div>
    <ErrorNotice error={products.error || categories.error} />{products.isPending && <Loading />}{products.data && <><div className="table-scroll"><table><thead><tr><th>Код</th><th>Продукт</th><th>Категорія</th><th>Стан</th><th>Облік</th><th>Ревізія</th></tr></thead><tbody>{products.data.items.map(item => <tr key={item.id}><td>{item.code}</td><td><Link className="record-link" to={`/products/${item.id}`}>{item.name}</Link></td><td>{item.category_name}</td><td><StatusBadge value={item.lifecycle} /></td><td>{item.tracking_mode}</td><td>{item.current_revision_id ? 'Випущена' : '—'}</td></tr>)}{!products.data.items.length && <tr><td colSpan={6}>Продуктів ще немає.</td></tr>}</tbody></table></div><Pagination page={page} total={products.data.total} pageSize={products.data.page_size} onChange={setPage} /></>}</>
}

function ProductCreate({ categories, onDone }: { categories: ProductCategory[]; onDone: () => void }) {
  const cache = useQueryClient(), [code, setCode] = useState(''), [name, setName] = useState(''), [categoryId, setCategoryId] = useState(categories[0]?.id ?? ''), [trackingMode, setTrackingMode] = useState<TrackingMode>('SERIAL')
  const mutation = useMutation({ mutationFn: () => send<Product>('/products', 'POST', { code, name, category_id: categoryId, description: '', lifecycle: 'DEVELOPMENT', tracking_mode: trackingMode }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['products'] }); onDone() } })
  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate() }
  return <form className="form-panel form-stack" onSubmit={submit}><h2>Новий продукт</h2><div className="editor-grid"><Field label="Код"><Input required value={code} onChange={event => setCode(event.target.value)} /></Field><Field label="Назва"><Input required value={name} onChange={event => setName(event.target.value)} /></Field><Field label="Категорія"><select className="form-input" value={categoryId} onChange={event => setCategoryId(event.target.value)}>{categories.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Облік"><select className="form-input" value={trackingMode} onChange={event => setTrackingMode(event.target.value as TrackingMode)}><option value="SERIAL">Серійний</option><option value="BATCH">Партіями</option><option value="QUANTITY">Кількісний</option></select></Field></div><ErrorNotice error={mutation.error} /><Button disabled={mutation.isPending}>Створити</Button></form>
}
