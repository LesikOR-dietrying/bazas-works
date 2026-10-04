import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { canEditEngineering } from '../engineering/hooks'
import { TestEquipmentPanel } from './TestEquipment'
import { TestMeasurements } from './TestMeasurements'
import type { TestRecord } from './types'
import type { FirmwareRevision } from '../engineering/types'
import { FilesPanel } from '../collaboration/FilesPanel'
import { CommentsPanel } from '../collaboration/CommentsPanel'
import { labelForCode } from '../../lib/labels'

const fieldNames: Record<string, string> = { location: 'Місце', weather: 'Погода', wind_speed_m_s: 'Вітер (м/с)', temperature_c: 'Температура (°C)', flight_time_minutes: 'Тривалість польоту (хв)', range_km: 'Дальність (км)', max_speed_kmh: 'Максимальна швидкість (км/год)', battery_remaining_percent: 'Залишок заряду (%)' }
function display(value: unknown): string { return typeof value === 'string' ? value : JSON.stringify(value) }
function Metadata({ title, values }: { title: string; values: Record<string, unknown> }) { return <section className="form-panel"><h2>{title}</h2>{Object.keys(values).length ? <dl className="detail-grid">{Object.entries(values).map(([key, value]) => <div key={key}><dt>{fieldNames[key] ?? key}</dt><dd>{display(value)}</dd></div>)}</dl> : <p>Даних ще немає.</p>}</section> }

export function TestDetail() {
  const { id = '' } = useParams(), { data: user } = useSession(), cache = useQueryClient(), navigate = useNavigate()
  const test = useQuery({ queryKey: ['test', id], enabled: canEditEngineering(user), queryFn: ({ signal }) => api<TestRecord>(`/tests/${id}`, { signal }) })
  const firmwareId = test.data?.firmware_revision_id
  const firmware = useQuery({ queryKey: ['firmware-revision', firmwareId], enabled: Boolean(firmwareId), queryFn: ({ signal }) => api<FirmwareRevision>(`/firmware/${firmwareId}`, { signal }) })
  const remove = useMutation({ mutationFn: () => send(`/tests/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['tests'] }); navigate('/tests') } })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Випробування доступні інженерам, менеджерам та адміністраторам.')} />
  if (test.isPending) return <Loading />
  if (!test.data) return <ErrorNotice error={test.error} />
  const data = test.data
  return <><div className="page-heading"><div><Link className="back-link" to="/tests">← Випробування</Link><h1>{data.name}</h1></div><div className="form-actions"><StatusBadge value={data.status} /><Button asChild variant="outline"><Link to={`/tests/${id}/edit`}>Редагувати</Link></Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити випробування «${data.name}» разом із його вимірюваннями? Цю дію неможливо скасувати.`)) remove.mutate() }}>Видалити</Button></div></div>
    <ErrorNotice error={remove.error || firmware.error} /><section className="form-panel"><h2>Відомості</h2><dl className="detail-grid"><div><dt>Тип</dt><dd>{labelForCode(data.test_type)}</dd></div><div><dt>Дата</dt><dd>{data.test_date ? new Date(data.test_date).toLocaleString('uk-UA') : 'Заплановано'}</dd></div><div><dt>Виконавець</dt><dd>{data.performed_by_name || (data.performed_by_id ? 'Ім’я недоступне' : '—')}</dd></div><div><dt>Проєкт</dt><dd>{data.project_id ? <Link className="record-link" to={`/projects/${data.project_id}`}>{data.project_name || 'Проєкт недоступний'}</Link> : '—'}</dd></div><div><dt>Конфігурація</dt><dd>{data.setup_id ? <Link className="record-link" to={`/setups/${data.setup_id}`}>{data.setup_name || 'Конфігурація недоступна'}</Link> : '—'}</dd></div><div><dt>Основний компонент</dt><dd>{data.component_id ? <Link className="record-link" to={`/components/${data.component_id}`}>{data.component_name || 'Компонент недоступний'}</Link> : '—'}</dd></div><div><dt>Версія прошивки</dt><dd>{firmware.data ? `${firmware.data.version_name} · ${firmware.data.firmware_version}` : data.firmware_revision_id ? 'Завантаження…' : '—'}</dd></div></dl><h2>Опис</h2><p className="description-text">{data.description || 'Опис ще не додано.'}</p><h2>Висновок</h2><p className="description-text">{data.conclusion || 'Висновок ще не додано.'}</p></section>
    <Metadata title="Умови" values={data.conditions} /><Metadata title="Підсумок" values={data.result_summary} />
    <TestEquipmentPanel testId={id} /><TestMeasurements testId={id} />
    <FilesPanel owner={{ kind: 'test', id }} /><CommentsPanel owner={{ kind: 'test', id }} />
  </>
}

