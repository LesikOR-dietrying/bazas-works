import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { canEditEngineering } from './hooks'
import { componentCategories } from './types'
import type { Component } from './types'

export function ComponentsPage() {
  const { data: user } = useSession()
  const [q, setQ] = useState(''), [category, setCategory] = useState(''), [page, setPage] = useState(1)
  const [sort, setSort] = useState('updated_at'), [direction, setDirection] = useState('desc')
  const params = new URLSearchParams({ q, page: String(page), sort, direction })
  if (category) params.set('category', category)
  const components = useQuery({ queryKey: ['components', params.toString()], enabled: canEditEngineering(user), queryFn: ({ signal }) => api<Page<Component>>(`/components?${params}`, { signal }) })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Каталог компонентів доступний інженерам, менеджерам та адміністраторам.')} />
  return <><div className="page-heading"><div><p className="eyebrow">ІНЖЕНЕРНИЙ КАТАЛОГ</p><h1>Компоненти</h1><p className="page-description">Спільні записи комплектуючих для різних конфігурацій.</p></div><Button asChild><Link to="/components/new">Новий компонент</Link></Button></div>
    <div className="filters"><Input aria-label="Пошук компонентів" placeholder="Назва, виробник або модель" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
      <select aria-label="Категорія компонента" className="form-input" value={category} onChange={e => { setCategory(e.target.value); setPage(1) }}><option value="">Усі категорії</option>{componentCategories.map(c => <option key={c}>{c}</option>)}</select>
      <select aria-label="Сортування компонентів" className="form-input" value={sort} onChange={e => { setSort(e.target.value); setPage(1) }}><option value="updated_at">За оновленням</option><option value="name">За назвою</option><option value="manufacturer">За виробником</option><option value="category">За категорією</option></select>
      <Button variant="outline" onClick={() => { setDirection(direction === 'asc' ? 'desc' : 'asc'); setPage(1) }}>{direction === 'asc' ? '↑ За зростанням' : '↓ За спаданням'}</Button></div>
    <ErrorNotice error={components.error} />{components.isPending && <Loading />}
    {components.data && <><div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Категорія</th><th>Виробник</th><th>Модель</th><th>Оновлено</th></tr></thead><tbody>{components.data.items.map(item => <tr key={item.id}><td><Link className="record-link" to={`/components/${item.id}`}>{item.name}</Link></td><td>{item.category}</td><td>{item.manufacturer || '—'}</td><td>{item.model || '—'}</td><td>{new Date(item.updated_at).toLocaleDateString('uk-UA')}</td></tr>)}{!components.data.items.length && <tr><td colSpan={5}>Компонентів не знайдено.</td></tr>}</tbody></table></div><Pagination page={page} total={components.data.total} pageSize={components.data.page_size} onChange={setPage} /></>}
  </>
}

