import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useComponentOptions } from './hooks'
import type { SetupComponent } from './types'

export function SetupBom({ setupId }: { setupId: string }) {
  const cache = useQueryClient(), options = useComponentOptions()
  const bom = useQuery({ queryKey: ['setup-components', setupId], queryFn: ({ signal }) => api<SetupComponent[]>(`/setups/${setupId}/components`, { signal }) })
  const [editing, setEditing] = useState<SetupComponent | null>(null)
  const [componentId, setComponentId] = useState(''), [quantity, setQuantity] = useState('1'), [position, setPosition] = useState(''), [notes, setNotes] = useState('')
  const [validation, setValidation] = useState('')
  const save = useMutation({ mutationFn: (body: object) => send<SetupComponent>(editing ? `/setups/${setupId}/components/${editing.id}` : `/setups/${setupId}/components`, editing ? 'PUT' : 'POST', body), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['setup-components', setupId] }); reset() } })
  const remove = useMutation({ mutationFn: (itemId: string) => send(`/setups/${setupId}/components/${itemId}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['setup-components', setupId] }) } })
  function reset() { setEditing(null); setComponentId(''); setQuantity('1'); setPosition(''); setNotes(''); setValidation('') }
  function edit(item: SetupComponent) { setEditing(item); setComponentId(item.component_id); setQuantity(String(item.quantity)); setPosition(item.position); setNotes(item.notes); setValidation('') }
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!componentId || !Number.isInteger(Number(quantity)) || Number(quantity) < 1) return setValidation('Оберіть компонент і вкажіть цілу кількість більше нуля.'); setValidation(''); save.mutate({ component_id: componentId, quantity: Number(quantity), position, notes }) }
  return <section className="form-panel"><h2>Склад компонентів (BOM)</h2><p className="page-description">Компоненти беруться зі спільного каталогу. Однаковий компонент можна додати на різні позиції.</p>
    <ErrorNotice error={bom.error || options.error || save.error || remove.error} />{bom.isPending && <Loading />}
    {bom.data && <div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Категорія</th><th>Кількість</th><th>Позиція</th><th>Примітки</th><th>Дії</th></tr></thead><tbody>{bom.data.map(item => <tr key={item.id}><td><Link className="record-link" to={`/components/${item.component_id}`}>{item.component.name}</Link></td><td>{item.component.category}</td><td>{item.quantity}</td><td>{item.position || '—'}</td><td>{item.notes || '—'}</td><td><div className="form-actions"><Button variant="outline" onClick={() => edit(item)}>Редагувати</Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Прибрати «${item.component.name}» зі складу сетапу?`)) remove.mutate(item.id) }}>Прибрати</Button></div></td></tr>)}{!bom.data.length && <tr><td colSpan={6}>Компонентів у складі ще немає.</td></tr>}</tbody></table></div>}
    <form className="form-stack" onSubmit={submit}><h2>{editing ? 'Редагувати позицію' : 'Додати компонент'}</h2><div className="editor-grid"><Field label="Компонент"><select className="form-input" required value={componentId} onChange={e => setComponentId(e.target.value)}><option value="">Оберіть із каталогу</option>{options.data?.map(item => <option key={item.id} value={item.id}>{item.name} · {item.manufacturer} {item.model}</option>)}</select></Field><Field label="Кількість"><Input type="number" min="1" step="1" required value={quantity} onChange={e => setQuantity(e.target.value)} /></Field><Field label="Позиція"><Input maxLength={100} value={position} onChange={e => setPosition(e.target.value)} placeholder="Наприклад: передній лівий" /></Field><Field label="Примітки"><Input value={notes} onChange={e => setNotes(e.target.value)} /></Field></div>{validation && <ErrorNotice error={new Error(validation)} />}<div className="form-actions"><Button type="submit" disabled={save.isPending || options.isPending || options.isError}>{editing ? 'Зберегти позицію' : 'Додати до складу'}</Button>{editing && <Button type="button" variant="outline" onClick={reset}>Скасувати</Button>}</div></form>
  </section>
}
