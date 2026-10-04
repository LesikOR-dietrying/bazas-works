import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'

const types = ['PROJECT', 'TASK', 'SETUP', 'COMPONENT', 'TEST'] as const
type SearchType = typeof types[number]
interface SearchResult { type: SearchType; id: string; title: string; context: string; path: string }
const labels: Record<SearchType, string> = { PROJECT: 'Проєкт', TASK: 'Задача', SETUP: 'Сетап', COMPONENT: 'Компонент', TEST: 'Випробування' }

export function SearchPage() {
  const [params, setParams] = useSearchParams(), term = params.get('q')?.trim() ?? '', type = params.get('type') ?? ''
  const [draftState, setDraftState] = useState({ term, draft: term }), page = Math.max(1, Number(params.get('page')) || 1)
  const draft = draftState.term === term ? draftState.draft : term
  const query = new URLSearchParams({ q: term, page: String(page) })
  if (type) query.set('type', type)
  const results = useQuery({ queryKey: ['search', query.toString()], enabled: Boolean(term), queryFn: ({ signal }) => api<Page<SearchResult>>(`/search?${query}`, { signal }) })
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setParams(draft.trim() ? { q: draft.trim() } : {}) }
  function changeType(next: string) { setParams({ q: term, ...(next ? { type: next } : {}) }) }
  function changePage(next: number) { setParams({ q: term, ...(type ? { type } : {}), page: String(next) }) }
  return <><div className="page-heading"><div><p className="eyebrow">ПОШУК</p><h1>Пошук у BAZA</h1><p className="page-description">Лише записи, до яких у вас є доступ.</p></div></div>
    <form role="search" className="filters" onSubmit={submit}><Input aria-label="Пошуковий запит" maxLength={200} value={draft} onChange={event => setDraftState({ term, draft: event.target.value })} placeholder="Проєкт, задача, компонент…" /><Button type="submit" disabled={!draft.trim()}>Знайти</Button></form>
    {term && <div className="filters"><select aria-label="Тип результату" className="form-input" value={type} onChange={event => changeType(event.target.value)}><option value="">Усі типи</option>{types.map(item => <option key={item} value={item}>{labels[item]}</option>)}</select></div>}
    <ErrorNotice error={results.error} />{term && results.isPending && <Loading />}{!term && <p className="page-description">Введіть запит, щоб знайти пов’язані записи.</p>}
    {results.data && <><div className="search-results">{results.data.items.map(item => <article className="search-result" key={`${item.type}-${item.id}`}><span className="status-badge">{labels[item.type]}</span><Link className="record-link" to={item.path.startsWith('/') && !item.path.startsWith('//') ? item.path : '/search'}>{item.title}</Link><p>{item.context}</p></article>)}{!results.data.items.length && <p>Нічого не знайдено.</p>}</div><Pagination page={page} total={results.data.total} pageSize={results.data.page_size} onChange={changePage} /></>}
  </>
}
