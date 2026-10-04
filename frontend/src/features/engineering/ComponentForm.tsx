import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { canEditEngineering, useComponent } from './hooks'
import { componentCategories } from './types'
import { labelForCode } from '../../lib/labels'
import type { Component, ComponentCategory } from './types'

interface SpecRow { key: string; value: string; original?: unknown }
const knownMotorSpecs: ReadonlyArray<{ key: string; label: string; unit: string }> = [
  { key: 'kv', label: 'KV', unit: 'об/хв/В' }, { key: 'max_current_a', label: 'Максимальний струм', unit: 'А' },
  { key: 'max_power_w', label: 'Максимальна потужність', unit: 'Вт' }, { key: 'weight_g', label: 'Маса', unit: 'г' },
]
const knownEscSpecs: ReadonlyArray<{ key: string; label: string; unit: string }> = [
  { key: 'continuous_current_a', label: 'Постійний струм', unit: 'А' },
  { key: 'burst_current_a', label: 'Піковий струм', unit: 'А' },
]
const scalarText = (value: unknown): string => typeof value === 'string' ? value : (JSON.stringify(value) ?? '')
const specText = (key: string, value: unknown) => key === 'recommended_propellers' && Array.isArray(value)
  ? value.filter(item => typeof item === 'string').join(', ') : scalarText(value)

export function ComponentFormPage() {
  const { id } = useParams(), { data: user } = useSession(), component = useComponent(id ?? '', canEditEngineering(user))
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Недостатньо прав для редагування компонентів.')} />
  if (id && component.isPending) return <Loading />
  if (component.error) return <ErrorNotice error={component.error} />
  return <ComponentForm key={id ?? 'new'} component={component.data} />
}

function ComponentForm({ component }: { component?: Component }) {
  const navigate = useNavigate(), cache = useQueryClient()
  const [category, setCategory] = useState<ComponentCategory>(component?.category ?? 'MOTOR')
  const [name, setName] = useState(component?.name ?? ''), [manufacturer, setManufacturer] = useState(component?.manufacturer ?? '')
  const [model, setModel] = useState(component?.model ?? ''), [description, setDescription] = useState(component?.description ?? '')
  const [datasheetUrl, setDatasheetUrl] = useState(component?.datasheet_url ?? ''), [notes, setNotes] = useState(component?.notes ?? '')
  const [specs, setSpecs] = useState<SpecRow[]>(Object.entries(component?.specifications ?? {}).map(([key, original]) => ({ key, value: specText(key, original), original })))
  const [validation, setValidation] = useState('')
  const mutation = useMutation({ mutationFn: (body: object) => send<Component>(component ? `/components/${component.id}` : '/components', component ? 'PUT' : 'POST', body),
    onSuccess: async saved => { await cache.invalidateQueries({ queryKey: ['components'] }); await cache.invalidateQueries({ queryKey: ['component-options'] }); cache.setQueryData(['component', saved.id], saved); navigate(`/components/${saved.id}`) } })
  function updateSpec(index: number, patch: Partial<SpecRow>) { setSpecs(rows => rows.map((row, i) => i === index ? { ...row, ...patch } : row)) }
  function setKnownSpec(key: string, value: string) {
    setSpecs(rows => {
      const index = rows.findIndex(row => row.key === key)
      return index < 0 ? [...rows, { key, value }] : rows.map((row, i) => i === index ? { ...row, value } : row)
    })
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!name.trim()) return setValidation('Вкажіть назву компонента.')
    const unique = new Set<string>(), specifications: Record<string, unknown> = {}
    for (const row of specs) {
      const key = row.key.trim()
      if (!key && !row.value.trim()) continue
      if (!key || unique.has(key)) return setValidation('Кожна характеристика повинна мати унікальну назву.')
      unique.add(key)
      const numeric = (category === 'MOTOR' ? knownMotorSpecs : category === 'ESC' ? knownEscSpecs : []).some(spec => spec.key === key)
      if (row.value.trim()) specifications[key] = numeric ? Number(row.value)
        : key === 'recommended_propellers' ? row.value.split(',').map(value => value.trim()).filter(Boolean)
          : row.original !== undefined && specText(key, row.original) === row.value ? row.original : row.value
    }
    setValidation('')
    mutation.mutate({ category, name: name.trim(), manufacturer, model, description, datasheet_url: datasheetUrl.trim() || null, notes, specifications })
  }
  const knownKeys = new Set([
    ...(category === 'MOTOR' ? knownMotorSpecs.map(spec => spec.key) : []),
    ...(category === 'ESC' ? knownEscSpecs.map(spec => spec.key) : []),
    ...(category === 'MOTOR' ? ['voltage', 'recommended_propellers'] : []),
    ...(category === 'ESC' ? ['voltage', 'firmware'] : []),
  ])
  const customSpecs = specs.map((row, index) => ({ row, index })).filter(({ row }) => !knownKeys.has(row.key))
  return <><div className="page-heading"><h1>{component ? 'Редагувати компонент' : 'Новий компонент'}</h1></div>
    <form className="form-panel form-stack" onSubmit={submit}><div className="editor-grid"><Field label="Назва"><Input maxLength={255} required value={name} onChange={e => setName(e.target.value)} /></Field><Field label="Категорія"><select className="form-input" value={category} onChange={e => setCategory(e.target.value as ComponentCategory)}>{componentCategories.map(value => <option key={value} value={value}>{labelForCode(value)}</option>)}</select></Field></div>
      <div className="editor-grid"><Field label="Виробник"><Input maxLength={255} value={manufacturer} onChange={e => setManufacturer(e.target.value)} /></Field><Field label="Модель"><Input maxLength={255} value={model} onChange={e => setModel(e.target.value)} /></Field></div>
      <Field label="Опис"><textarea className="form-input" value={description} onChange={e => setDescription(e.target.value)} /></Field>
      {(category === 'MOTOR' || category === 'ESC') && <section><h2>{category === 'MOTOR' ? 'Характеристики двигуна' : 'Характеристики ESC'}</h2><div className="editor-grid">{(category === 'MOTOR' ? knownMotorSpecs : knownEscSpecs).map(spec => <Field key={spec.key} label={`${spec.label} (${spec.unit})`}><Input type="number" min="0" step="any" value={specs.find(row => row.key === spec.key)?.value ?? ''} onChange={e => setKnownSpec(spec.key, e.target.value)} /></Field>)}<Field label="Робоча напруга"><Input value={specs.find(row => row.key === 'voltage')?.value ?? ''} placeholder={category === 'MOTOR' ? 'Наприклад, 12S' : 'Наприклад, 6–12S'} onChange={e => setKnownSpec('voltage', e.target.value)} /></Field>{category === 'MOTOR' ? <Field label="Рекомендовані пропелери"><Input value={specs.find(row => row.key === 'recommended_propellers')?.value ?? ''} placeholder="15.5x5.8, 17x6" onChange={e => setKnownSpec('recommended_propellers', e.target.value)} /></Field> : <Field label="Прошивка ESC"><Input value={specs.find(row => row.key === 'firmware')?.value ?? ''} placeholder="Наприклад, AM32" onChange={e => setKnownSpec('firmware', e.target.value)} /></Field>}</div></section>}
      <section><h2>Додаткові характеристики</h2><p className="page-description">Назва і значення зберігаються в характеристиках компонента.</p>{customSpecs.map(({ row, index }) => <div className="editor-grid spec-row" key={index}><Field label="Назва характеристики"><Input value={row.key} onChange={e => updateSpec(index, { key: e.target.value })} /></Field><Field label="Значення"><Input value={row.value} onChange={e => updateSpec(index, { value: e.target.value })} /></Field><Button type="button" variant="outline" onClick={() => setSpecs(rows => rows.filter((_, i) => i !== index))}>Прибрати</Button></div>)}<Button type="button" variant="outline" onClick={() => setSpecs(rows => [...rows, { key: '', value: '' }])}>Додати характеристику</Button></section>
      <Field label="Посилання на datasheet"><Input type="url" value={datasheetUrl} onChange={e => setDatasheetUrl(e.target.value)} /></Field>
      <Field label="Примітки"><textarea className="form-input" value={notes} onChange={e => setNotes(e.target.value)} /></Field>
      {validation && <ErrorNotice error={new Error(validation)} />}<ErrorNotice error={mutation.error} /><div className="form-actions"><Button type="submit" disabled={mutation.isPending}>Зберегти компонент</Button><Button asChild variant="outline"><Link to={component ? `/components/${component.id}` : '/components'}>Скасувати</Link></Button></div>
    </form></>
}

