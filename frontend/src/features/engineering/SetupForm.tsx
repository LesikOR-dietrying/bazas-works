import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { canEditEngineering, useSetup } from './hooks'
import { setupStatuses } from './types'
import { labelForCode } from '../../lib/labels'
import type { Setup, SetupStatus } from './types'
import { MetadataFields } from '../tests/MetadataFields'

type TextKey = 'name' | 'drone_class' | 'version' | 'description' | 'battery_description' | 'propeller_description' | 'firmware_type' | 'firmware_version' | 'notes'
type NumberKey = 'weight_kg' | 'payload_kg' | 'battery_voltage' | 'battery_capacity_ah' | 'flight_time_minutes' | 'average_current_a' | 'max_current_a'
const textFields: ReadonlyArray<{ key: TextKey; label: string; required?: boolean }> = [
  { key: 'name', label: 'Назва', required: true }, { key: 'drone_class', label: 'Клас дрона', required: true },
  { key: 'version', label: 'Версія конфігурації', required: true }, { key: 'battery_description', label: 'Акумулятор' },
  { key: 'propeller_description', label: 'Пропелер' }, { key: 'firmware_type', label: 'Тип прошивки' },
  { key: 'firmware_version', label: 'Версія прошивки' },
]
const numberFields: ReadonlyArray<{ key: NumberKey; label: string }> = [
  { key: 'weight_kg', label: 'Маса (кг)' }, { key: 'payload_kg', label: 'Корисне навантаження (кг)' },
  { key: 'battery_voltage', label: 'Напруга батареї (В)' }, { key: 'battery_capacity_ah', label: 'Ємність батареї (А·год)' },
  { key: 'flight_time_minutes', label: 'Час польоту (хв)' }, { key: 'average_current_a', label: 'Середній струм (А)' },
  { key: 'max_current_a', label: 'Максимальний струм (А)' },
]
type Draft = Record<TextKey | NumberKey, string> & { status: SetupStatus }
function initial(setup?: Setup): Draft {
  return { name: setup?.name ?? '', drone_class: setup?.drone_class ?? '', version: setup?.version ?? '', status: setup?.status ?? 'DEVELOPMENT',
    description: setup?.description ?? '', battery_description: setup?.battery_description ?? '', propeller_description: setup?.propeller_description ?? '',
    firmware_type: setup?.firmware_type ?? '', firmware_version: setup?.firmware_version ?? '', notes: setup?.notes ?? '',
    weight_kg: String(setup?.weight_kg ?? ''), payload_kg: String(setup?.payload_kg ?? ''), battery_voltage: String(setup?.battery_voltage ?? ''),
    battery_capacity_ah: String(setup?.battery_capacity_ah ?? ''), flight_time_minutes: String(setup?.flight_time_minutes ?? ''),
    average_current_a: String(setup?.average_current_a ?? ''), max_current_a: String(setup?.max_current_a ?? '') }
}

export function SetupFormPage() {
  const { id } = useParams(), { data: user } = useSession(), setup = useSetup(id ?? '', canEditEngineering(user))
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Недостатньо прав для редагування сетапів.')} />
  if (id && setup.isPending) return <Loading />
  if (setup.error) return <ErrorNotice error={setup.error} />
  return <SetupForm key={id ?? 'new'} setup={setup.data} />
}

function SetupForm({ setup }: { setup?: Setup }) {
  const [draft, setDraft] = useState<Draft>(() => initial(setup)), [validation, setValidation] = useState('')
  const [attributes, setAttributes] = useState<Record<string, unknown>>(setup?.attributes ?? {})
  const navigate = useNavigate(), cache = useQueryClient()
  const mutation = useMutation({ mutationFn: (body: object) => send<Setup>(setup ? `/setups/${setup.id}` : '/setups', setup ? 'PUT' : 'POST', body), onSuccess: async saved => { await cache.invalidateQueries({ queryKey: ['setups'] }); await cache.invalidateQueries({ queryKey: ['setup-options'] }); cache.setQueryData(['setup', saved.id], saved); navigate(`/setups/${saved.id}`) } })
  function set(key: keyof Draft, value: string) { setDraft(current => ({ ...current, [key]: value })) }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft.name.trim() || !draft.drone_class.trim() || !draft.version.trim()) return setValidation('Назва, клас і версія обов’язкові.')
    if (draft.average_current_a && draft.max_current_a && Number(draft.max_current_a) < Number(draft.average_current_a)) return setValidation('Максимальний струм не може бути меншим за середній.')
    const body: Record<string, unknown> = { ...draft, attributes }
    for (const { key } of numberFields) body[key] = draft[key] === '' ? null : Number(draft[key])
    setValidation('')
    mutation.mutate(body)
  }
  return <><div className="page-heading"><h1>{setup ? 'Редагувати сетап' : 'Новий сетап'}</h1></div><form className="form-panel form-stack" onSubmit={submit}>
    <div className="editor-grid">{textFields.slice(0, 3).map(({ key, label, required }) => <Field key={key} label={label}><Input maxLength={255} required={required} value={draft[key]} onChange={e => set(key, e.target.value)} /></Field>)}<Field label="Статус"><select className="form-input" value={draft.status} onChange={e => set('status', e.target.value)}>{setupStatuses.map(status => <option key={status} value={status}>{labelForCode(status)}</option>)}</select></Field></div>
    <Field label="Опис"><textarea className="form-input" value={draft.description} onChange={e => set('description', e.target.value)} /></Field>
    <h2>Параметри конфігурації</h2><div className="editor-grid">{numberFields.map(({ key, label }) => <Field key={key} label={label}><Input type="number" min="0" step="any" value={draft[key]} onChange={e => set(key, e.target.value)} /></Field>)}{textFields.slice(3).map(({ key, label }) => <Field key={key} label={label}><Input maxLength={255} value={draft[key]} onChange={e => set(key, e.target.value)} /></Field>)}</div>
    <MetadataFields title="Інші характеристики" values={attributes} onChange={setAttributes} />
    <Field label="Примітки"><textarea className="form-input" value={draft.notes} onChange={e => set('notes', e.target.value)} /></Field>
    <p className="page-description">Склад компонентів, проєкти та ревізії прошивки додаються після створення сетапу.</p>
    {validation && <ErrorNotice error={new Error(validation)} />}<ErrorNotice error={mutation.error} /><div className="form-actions"><Button type="submit" disabled={mutation.isPending}>Зберегти сетап</Button><Button asChild variant="outline"><Link to={setup ? `/setups/${setup.id}` : '/setups'}>Скасувати</Link></Button></div>
  </form></>
}

