import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { useUserOptions, useProjectOptions } from '../projects/hooks'
import { canEditEngineering, useComponentOptions, useSetupOptions } from '../engineering/hooks'
import type { SetupOption, FirmwareRevision } from '../engineering/types'
import { testStatuses, testTypes } from './types'
import type { TestRecord, TestStatus, TestType } from './types'
import { MetadataFields } from './MetadataFields'
import { labelForCode } from '../../lib/labels'

type TextField = 'name' | 'description' | 'conclusion'
type IdField = 'project_id' | 'branch_id' | 'setup_id' | 'component_id' | 'firmware_revision_id' | 'performed_by_id'
type Draft = Record<TextField | IdField, string> & { test_type: TestType; status: TestStatus; test_date: string }
function localDate(value: string | null) { if (!value) return ''; const date = new Date(value); date.setMinutes(date.getMinutes() - date.getTimezoneOffset()); return date.toISOString().slice(0, 16) }
function initial(test: TestRecord | undefined, query: URLSearchParams): Draft { return { name: test?.name ?? '', test_type: test?.test_type ?? (testTypes.find(type => type === query.get('test_type')) ?? 'MOTOR_BENCH'), project_id: test?.project_id ?? query.get('project_id') ?? '', branch_id: test?.branch_id ?? query.get('branch_id') ?? '', setup_id: test?.setup_id ?? query.get('setup_id') ?? '', component_id: test?.component_id ?? query.get('component_id') ?? '', firmware_revision_id: test?.firmware_revision_id ?? '', performed_by_id: test?.performed_by_id ?? '', test_date: localDate(test?.test_date ?? null), status: test?.status ?? 'PLANNED', description: test?.description ?? '', conclusion: test?.conclusion ?? '' } }
function objectField(source: Record<string, unknown> | undefined, key: string) { const value = source?.[key]; return typeof value === 'string' || typeof value === 'number' ? String(value) : '' }
const flightConditions = [{ key: 'location', label: 'Місце', numeric: false }, { key: 'weather', label: 'Погода', numeric: false }, { key: 'wind_speed_m_s', label: 'Швидкість вітру (м/с)', numeric: true }, { key: 'temperature_c', label: 'Температура повітря (°C)', numeric: true }] as const
const flightResults = [{ key: 'flight_time_minutes', label: 'Тривалість польоту (хв)', numeric: true }, { key: 'range_km', label: 'Дальність (км)', numeric: true }, { key: 'max_speed_kmh', label: 'Максимальна швидкість (км/год)', numeric: true }, { key: 'battery_remaining_percent', label: 'Заряд після польоту (%)', numeric: true }] as const

export function TestFormPage() {
  const { id } = useParams(), { data: user } = useSession()
  const test = useQuery({ queryKey: ['test', id], enabled: Boolean(id) && canEditEngineering(user), queryFn: ({ signal }) => api<TestRecord>(`/tests/${id}`, { signal }) })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Недостатньо прав для редагування випробувань.')} />
  if (id && test.isPending) return <Loading />
  if (test.error) return <ErrorNotice error={test.error} />
  return <TestForm key={id ?? 'new'} test={test.data} />
}

function TestForm({ test }: { test?: TestRecord }) {
  const [query] = useSearchParams(), { data: me } = useSession(), navigate = useNavigate(), cache = useQueryClient()
  const [draft, setDraft] = useState<Draft>(() => initial(test, query))
  const [conditions, setConditions] = useState<Record<string, unknown>>(test?.conditions ?? {})
  const [summary, setSummary] = useState<Record<string, unknown>>(test?.result_summary ?? {})
  const [validation, setValidation] = useState('')
  const projects = useProjectOptions(), setupOptions = useSetupOptions(), components = useComponentOptions(), users = useUserOptions()
  const linkedSetups = useQuery({ queryKey: ['project-setups', draft.project_id], enabled: Boolean(draft.project_id), queryFn: ({ signal }) => api<SetupOption[]>(`/projects/${draft.project_id}/setups`, { signal }) })
  const firmware = useQuery({ queryKey: ['firmware', draft.setup_id, 'options'], enabled: Boolean(draft.setup_id), queryFn: ({ signal }) => api<Page<FirmwareRevision>>(`/firmware?setup_id=${draft.setup_id}&page_size=100`, { signal }) })
  const save = useMutation({ mutationFn: (body: object) => send<TestRecord>(test ? `/tests/${test.id}` : '/tests', test ? 'PUT' : 'POST', body), onSuccess: async saved => { await cache.invalidateQueries({ queryKey: ['tests'] }); cache.setQueryData(['test', saved.id], saved); navigate(`/tests/${saved.id}`) } })
  function set(key: keyof Draft, value: string) { setDraft(current => ({ ...current, [key]: value })) }
  function setObject(source: 'conditions' | 'summary', key: string, value: string, numeric: boolean) {
    const updater = source === 'conditions' ? setConditions : setSummary
    updater(current => { const next = { ...current }; if (value === '') delete next[key]; else next[key] = numeric ? Number(value) : value; return next })
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!draft.name.trim()) return setValidation('Вкажіть назву випробування.')
    if (draft.test_type === 'MOTOR_BENCH' && !draft.component_id) return setValidation('Для стендового тесту оберіть двигун.')
    if ((draft.test_type === 'FLIGHT' || draft.test_type === 'ENDURANCE') && !draft.setup_id) return setValidation('Для польоту оберіть сетап.')
    if (!draft.project_id && !draft.setup_id && !draft.component_id) return setValidation('Оберіть проєкт, сетап або компонент.')
    if (draft.status !== 'PLANNED' && (!draft.performed_by_id || !draft.test_date)) return setValidation('Для розпочатого тесту вкажіть виконавця та дату.')
    if (draft.project_id && draft.setup_id && !linkedSetups.data?.some(item => item.id === draft.setup_id)) return setValidation('Сетап повинен бути прив’язаний до проєкту.')
    if (draft.firmware_revision_id && !firmware.data?.items.some(item => item.id === draft.firmware_revision_id)) return setValidation('Оберіть ревізію цього сетапу.')
    setValidation('')
    save.mutate({ ...draft, name: draft.name.trim(), project_id: draft.project_id || null, branch_id: draft.branch_id || null, setup_id: draft.setup_id || null, component_id: draft.component_id || null, firmware_revision_id: draft.firmware_revision_id || null, performed_by_id: draft.performed_by_id || null, test_date: draft.test_date ? new Date(draft.test_date).toISOString() : null, conditions, result_summary: summary })
  }
  const setups = draft.project_id ? linkedSetups.data ?? [] : setupOptions.data ?? []
  const subjectComponents = components.data?.filter(item => draft.test_type === 'MOTOR_BENCH' ? item.category === 'MOTOR' : draft.test_type === 'ESC_BENCH' ? item.category === 'ESC' : true) ?? []
  return <><div className="page-heading"><h1>{test ? 'Редагувати випробування' : 'Нове випробування'}</h1></div><form className="form-panel form-stack" onSubmit={submit}>
    <div className="editor-grid"><Field label="Назва"><Input required maxLength={255} value={draft.name} onChange={e => set('name', e.target.value)} /></Field><Field label="Тип"><select className="form-input" value={draft.test_type} onChange={e => setDraft(current => ({ ...current, test_type: e.target.value as TestType, component_id: '' }))}>{testTypes.map(type => <option key={type} value={type}>{labelForCode(type)}</option>)}</select></Field><Field label="Статус"><select className="form-input" value={draft.status} onChange={e => { set('status', e.target.value); if (e.target.value !== 'PLANNED' && !draft.performed_by_id && me) set('performed_by_id', me.id) }}>{testStatuses.map(status => <option key={status} value={status}>{labelForCode(status)}</option>)}</select></Field></div>
    <div className="editor-grid"><Field label="Проєкт"><select className="form-input" value={draft.project_id} onChange={e => setDraft(current => ({ ...current, project_id: e.target.value, setup_id: '', firmware_revision_id: '' }))}><option value="">Без проєкту</option>{projects.data?.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Сетап"><select className="form-input" value={draft.setup_id} onChange={e => setDraft(current => ({ ...current, setup_id: e.target.value, firmware_revision_id: '' }))}><option value="">Без сетапу</option>{setups.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select></Field><Field label="Основний компонент"><select className="form-input" value={draft.component_id} onChange={e => set('component_id', e.target.value)}><option value="">Без компонента</option>{subjectComponents.map(item => <option key={item.id} value={item.id}>{item.name} · {item.category}</option>)}</select></Field><Field label="Ревізія прошивки"><select className="form-input" disabled={!draft.setup_id} value={draft.firmware_revision_id} onChange={e => set('firmware_revision_id', e.target.value)}><option value="">Без ревізії</option>{firmware.data?.items.map(item => <option key={item.id} value={item.id}>{item.version_name} · {item.firmware_version}</option>)}</select></Field></div>
    {draft.branch_id && <p className="page-description">Випробування належить R&D гілці. <Link className="record-link" to={`/rnd/branches/${draft.branch_id}`}>Відкрити гілку</Link></p>}
    <div className="editor-grid"><Field label="Виконавець"><select className="form-input" value={draft.performed_by_id} onChange={e => set('performed_by_id', e.target.value)}><option value="">Ще не призначено</option>{users.data?.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select></Field><Field label="Дата тесту (місцевий час)"><Input type="datetime-local" value={draft.test_date} onChange={e => set('test_date', e.target.value)} /></Field></div>
    <Field label="Опис"><textarea className="form-input" value={draft.description} onChange={e => set('description', e.target.value)} /></Field>
    {(draft.test_type === 'FLIGHT' || draft.test_type === 'ENDURANCE') && <><h2>Умови польоту</h2><div className="editor-grid">{flightConditions.map(field => <Field key={field.key} label={field.label}><Input type={field.numeric ? 'number' : 'text'} step={field.numeric ? 'any' : undefined} value={objectField(conditions, field.key)} onChange={e => setObject('conditions', field.key, e.target.value, field.numeric)} /></Field>)}</div><h2>Підсумок польоту</h2><div className="editor-grid">{flightResults.map(field => <Field key={field.key} label={field.label}><Input type="number" min="0" step="any" value={objectField(summary, field.key)} onChange={e => setObject('summary', field.key, e.target.value, field.numeric)} /></Field>)}</div></>}
    <MetadataFields title="Інші умови" values={conditions} onChange={setConditions} hiddenKeys={draft.test_type === 'FLIGHT' || draft.test_type === 'ENDURANCE' ? flightConditions.map(field => field.key) : []} />
    <MetadataFields title="Інші результати" values={summary} onChange={setSummary} hiddenKeys={draft.test_type === 'FLIGHT' || draft.test_type === 'ENDURANCE' ? flightResults.map(field => field.key) : []} />
    <Field label="Висновок"><textarea className="form-input" value={draft.conclusion} onChange={e => set('conclusion', e.target.value)} /></Field>
    <p className="page-description">Допоміжне обладнання та точки вимірювань додаються на сторінці створеного випробування.</p>
    {validation && <ErrorNotice error={new Error(validation)} />}<ErrorNotice error={save.error || projects.error || setupOptions.error || components.error || users.error || linkedSetups.error || firmware.error} /><div className="form-actions"><Button type="submit" disabled={save.isPending || projects.isPending || components.isPending || users.isPending}>Зберегти випробування</Button><Button asChild variant="outline"><Link to={test ? `/tests/${test.id}` : '/tests'}>Скасувати</Link></Button></div>
  </form></>
}

