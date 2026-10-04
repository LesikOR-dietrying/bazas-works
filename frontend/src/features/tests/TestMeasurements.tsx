import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { measurementFields } from './types'
import type { MeasurementField, TestMeasurement } from './types'

type Draft = Record<MeasurementField, string> & { sequence: string }
function blank(sequence: number | ''): Draft { return { sequence: String(sequence), throttle_percent: '', voltage_v: '', current_a: '', power_w: '', rpm: '', thrust_kg: '', efficiency_g_w: '', motor_temperature_c: '', esc_temperature_c: '', timestamp_seconds: '' } }
function fromMeasurement(item: TestMeasurement): Draft { return { sequence: String(item.sequence), throttle_percent: item.throttle_percent ?? '', voltage_v: item.voltage_v ?? '', current_a: item.current_a ?? '', power_w: item.power_w ?? '', rpm: item.rpm ?? '', thrust_kg: item.thrust_kg ?? '', efficiency_g_w: item.efficiency_g_w ?? '', motor_temperature_c: item.motor_temperature_c ?? '', esc_temperature_c: item.esc_temperature_c ?? '', timestamp_seconds: item.timestamp_seconds ?? '' } }
function readNumber(value: string | null) { return value === null ? null : Number(value) }

export function TestMeasurements({ testId }: { testId: string }) {
  const cache = useQueryClient(), [editing, setEditing] = useState<TestMeasurement | null>(null), [draft, setDraft] = useState<Draft>(() => blank('')), [validation, setValidation] = useState('')
  const measurements = useQuery({ queryKey: ['test-measurements', testId], queryFn: ({ signal }) => api<TestMeasurement[]>(`/tests/${testId}/measurements`, { signal }) })
  const save = useMutation({ mutationFn: (body: object) => send<TestMeasurement>(editing ? `/tests/${testId}/measurements/${editing.id}` : `/tests/${testId}/measurements`, editing ? 'PUT' : 'POST', body), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['test-measurements', testId] }); reset() } })
  const remove = useMutation({ mutationFn: (id: string) => send(`/tests/${testId}/measurements/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['test-measurements', testId] }) } })
  function reset() { setEditing(null); setDraft(blank((measurements.data?.reduce((max, item) => Math.max(max, item.sequence), -1) ?? -1) + 1)); setValidation('') }
  function edit(item: TestMeasurement) { setEditing(item); setDraft(fromMeasurement(item)); setValidation('') }
  function set(key: keyof Draft, value: string) { setDraft(current => ({ ...current, [key]: value })) }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const sequence = draft.sequence === '' ? Math.max(-1, ...(measurements.data ?? []).map(item => item.sequence)) + 1 : Number(draft.sequence)
    if (!Number.isInteger(sequence) || sequence < 0) return setValidation('Номер точки повинен бути цілим невід’ємним числом.')
    if (draft.throttle_percent && (Number(draft.throttle_percent) < 0 || Number(draft.throttle_percent) > 100)) return setValidation('Газ має бути в межах 0–100%.')
    if (measurementFields.some(([key]) => key !== 'motor_temperature_c' && key !== 'esc_temperature_c' && draft[key] && Number(draft[key]) < 0)) return setValidation('Вимірювання, крім температур, не можуть бути від’ємними.')
    setValidation('')
    const body: Record<string, string | number | null> = { sequence }
    for (const [key] of measurementFields) body[key] = draft[key] === '' ? null : Number(draft[key])
    save.mutate(body)
  }
  const rows = [...(measurements.data ?? [])].sort((a, b) => a.sequence - b.sequence)
  const chart = rows.map(item => ({ sequence: item.sequence, throttle: readNumber(item.throttle_percent), thrust: readNumber(item.thrust_kg), current: readNumber(item.current_a), power: readNumber(item.power_w), efficiency: readNumber(item.efficiency_g_w) }))
  return <><section className="form-panel"><h2>Точки вимірювань</h2><p className="page-description">Порожня клітинка означає, що значення не вимірювали. Нуль зберігається як реальний результат.</p><ErrorNotice error={measurements.error || save.error || remove.error} />{measurements.isPending && <Loading />}
    {measurements.data && <div className="table-scroll"><table><thead><tr><th>№</th>{measurementFields.map(([key, label]) => <th key={key}>{label}</th>)}<th>Дії</th></tr></thead><tbody>{rows.map(item => <tr key={item.id}><td>{item.sequence}</td>{measurementFields.map(([key]) => <td key={key}>{item[key] ?? '—'}</td>)}<td><div className="form-actions"><Button variant="outline" onClick={() => edit(item)}>Редагувати</Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити точку №${item.sequence}?`)) remove.mutate(item.id) }}>Видалити</Button></div></td></tr>)}{!rows.length && <tr><td colSpan={12}>Точок ще немає.</td></tr>}</tbody></table></div>}
    <form className="form-stack" onSubmit={submit}><h2>{editing ? `Редагувати точку №${editing.sequence}` : 'Додати точку'}</h2><div className="measurement-grid"><Field label="Номер точки"><Input type="number" min="0" step="1" placeholder="Наступний номер автоматично" value={draft.sequence} onChange={e => set('sequence', e.target.value)} /></Field>{measurementFields.map(([key, label]) => <Field key={key} label={label}><Input type="number" step="any" min={key === 'motor_temperature_c' || key === 'esc_temperature_c' ? undefined : '0'} max={key === 'throttle_percent' ? '100' : undefined} value={draft[key]} onChange={e => set(key, e.target.value)} /></Field>)}</div>{validation && <ErrorNotice error={new Error(validation)} />}<div className="form-actions"><Button type="submit" disabled={save.isPending}>{editing ? 'Зберегти точку' : 'Додати точку'}</Button>{editing && <Button variant="outline" type="button" onClick={reset}>Скасувати</Button>}</div></form>
  </section>
    {chart.length > 0 && <section className="form-panel"><h2>Графіки вимірювань</h2><p className="page-description">Графіки побудовані з точок вище; окремих результатів для них не зберігаємо.</p><div className="chart-grid"><div role="img" aria-label="Графік тяги залежно від газу"><h3>Тяга (кг)</h3><ResponsiveContainer width="100%" height={260}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="throttle" label={{ value: 'Газ, %', position: 'insideBottom', offset: -5 }} /><YAxis /><Tooltip /><Line type="monotone" dataKey="thrust" stroke="#426540" connectNulls={false} name="Тяга, кг" /></LineChart></ResponsiveContainer></div><div role="img" aria-label="Графік струму за точками"><h3>Струм (А)</h3><ResponsiveContainer width="100%" height={260}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="sequence" /><YAxis /><Tooltip /><Line type="monotone" dataKey="current" stroke="#2a5c86" connectNulls={false} name="Струм, А" /></LineChart></ResponsiveContainer></div><div role="img" aria-label="Графік ефективності за точками"><h3>Ефективність (г/Вт)</h3><ResponsiveContainer width="100%" height={260}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="sequence" /><YAxis /><Tooltip /><Line type="monotone" dataKey="efficiency" stroke="#986b2d" connectNulls={false} name="Ефективність, г/Вт" /></LineChart></ResponsiveContainer></div><div role="img" aria-label="Графік потужності за точками"><h3>Потужність (Вт)</h3><ResponsiveContainer width="100%" height={260}><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="sequence" /><YAxis /><Tooltip /><Line type="monotone" dataKey="power" stroke="#805898" connectNulls={false} name="Потужність, Вт" /></LineChart></ResponsiveContainer></div></div></section>}
  </>
}
