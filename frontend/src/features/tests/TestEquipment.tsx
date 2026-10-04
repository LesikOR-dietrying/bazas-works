import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useComponentOptions } from '../engineering/hooks'
import { equipmentRoles } from './types'
import { labelForCode } from '../../lib/labels'
import type { EquipmentRole, TestEquipment } from './types'

export function TestEquipmentPanel({ testId }: { testId: string }) {
  const [componentId, setComponentId] = useState(''), [role, setRole] = useState<EquipmentRole>('ESC'), [notes, setNotes] = useState('')
  const cache = useQueryClient(), components = useComponentOptions()
  const items = useQuery({ queryKey: ['test-components', testId], queryFn: ({ signal }) => api<TestEquipment[]>(`/tests/${testId}/components`, { signal }) })
  const create = useMutation({ mutationFn: () => send<TestEquipment>(`/tests/${testId}/components`, 'POST', { component_id: componentId, role, notes }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['test-components', testId] }); setComponentId(''); setNotes('') } })
  const remove = useMutation({ mutationFn: (id: string) => send(`/tests/${testId}/components/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['test-components', testId] }) } })
  const eligible = components.data?.filter(item => role === 'OTHER' || item.category === role) ?? []
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (componentId) create.mutate() }
  return <section className="form-panel"><h2>Допоміжне обладнання</h2><ErrorNotice error={items.error || components.error || create.error || remove.error} />{items.isPending && <Loading />}
    {items.data && <div className="table-scroll"><table><thead><tr><th>Компонент</th><th>Роль</th><th>Примітки</th><th>Дії</th></tr></thead><tbody>{items.data.map(item => <tr key={item.id}><td><Link className="record-link" to={`/components/${item.component_id}`}>{item.component.name}</Link></td><td>{item.role}</td><td>{item.notes || '—'}</td><td><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Прибрати «${item.component.name}» з обладнання тесту?`)) remove.mutate(item.id) }}>Прибрати</Button></td></tr>)}{!items.data.length && <tr><td colSpan={4}>Допоміжного обладнання ще немає.</td></tr>}</tbody></table></div>}
    <form className="form-stack" onSubmit={submit}><h2>Додати обладнання</h2><div className="editor-grid"><Field label="Роль"><select className="form-input" value={role} onChange={e => { setRole(e.target.value as EquipmentRole); setComponentId('') }}>{equipmentRoles.map(value => <option key={value} value={value}>{labelForCode(value)}</option>)}</select></Field><Field label="Компонент"><select className="form-input" required value={componentId} onChange={e => setComponentId(e.target.value)}><option value="">Оберіть компонент</option>{eligible.map(item => <option key={item.id} value={item.id}>{item.name} · {item.manufacturer} {item.model}</option>)}</select></Field><Field label="Примітки"><Input value={notes} onChange={e => setNotes(e.target.value)} /></Field></div><Button type="submit" disabled={create.isPending || components.isPending || components.isError}>Додати</Button></form>
  </section>
}
