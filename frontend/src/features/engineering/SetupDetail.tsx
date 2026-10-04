import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { send } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { canEditEngineering, useSetup } from './hooks'
import { SetupBom } from './SetupBom'
import { SetupFirmware } from './SetupFirmware'
import type { Setup } from './types'
import { TestsPage } from '../tests/TestsPage'
import { FilesPanel } from '../collaboration/FilesPanel'
import { CommentsPanel } from '../collaboration/CommentsPanel'

const tabs = ['Огляд', 'Компоненти', 'Прошивка', 'Випробування', 'Польоти', 'Файли', 'Коментарі'] as const
type Tab = typeof tabs[number]
function value(number: string | null, unit: string) { return number === null ? '—' : `${number} ${unit}` }

export function SetupDetail() {
  const { id = '' } = useParams(), { data: user } = useSession(), setup = useSetup(id, canEditEngineering(user))
  const [tab, setTab] = useState<Tab>('Огляд'), [newVersion, setNewVersion] = useState('')
  const navigate = useNavigate(), cache = useQueryClient()
  const remove = useMutation({ mutationFn: () => send(`/setups/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['setups'] }); await cache.invalidateQueries({ queryKey: ['setup-options'] }); navigate('/setups') } })
  const clone = useMutation({ mutationFn: (version: string) => send<Setup>(`/setups/${id}/clone`, 'POST', { version }), onSuccess: async saved => { await cache.invalidateQueries({ queryKey: ['setups'] }); await cache.invalidateQueries({ queryKey: ['setup-options'] }); navigate(`/setups/${saved.id}`) } })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Конфігурації доступні інженерам, менеджерам та адміністраторам.')} />
  if (setup.isPending) return <Loading />
  if (!setup.data) return <ErrorNotice error={setup.error} />
  const data = setup.data
  return <><div className="page-heading"><div><Link className="back-link" to="/setups">← Сетапи</Link><h1>{data.name} · {data.version}</h1></div><div className="form-actions"><StatusBadge value={data.status} /><Button asChild variant="outline"><Link to={`/setups/${id}/edit`}>Редагувати</Link></Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити сетап «${data.name} · ${data.version}»? Пов’язані з історією конфігурації сервер захищає від видалення.`)) remove.mutate() }}>Видалити</Button></div></div>
    <ErrorNotice error={remove.error || clone.error} /><div className="tabs" role="tablist" aria-label="Розділи сетапу">{tabs.map(name => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'selected' : ''} onClick={() => setTab(name)}>{name}</button>)}</div>
    {tab === 'Огляд' && <><section className="form-panel"><h2>Конфігурація</h2><p className="description-text">{data.description || 'Опис ще не додано.'}</p><dl className="detail-grid"><div><dt>Клас</dt><dd>{data.drone_class}</dd></div><div><dt>Маса</dt><dd>{value(data.weight_kg, 'кг')}</dd></div><div><dt>Навантаження</dt><dd>{value(data.payload_kg, 'кг')}</dd></div><div><dt>Батарея</dt><dd>{data.battery_description || '—'}</dd></div><div><dt>Напруга</dt><dd>{value(data.battery_voltage, 'В')}</dd></div><div><dt>Ємність</dt><dd>{value(data.battery_capacity_ah, 'А·год')}</dd></div><div><dt>Пропелер</dt><dd>{data.propeller_description || '—'}</dd></div><div><dt>Час польоту</dt><dd>{value(data.flight_time_minutes, 'хв')}</dd></div><div><dt>Середній струм</dt><dd>{value(data.average_current_a, 'А')}</dd></div><div><dt>Максимальний струм</dt><dd>{value(data.max_current_a, 'А')}</dd></div><div><dt>Тип прошивки</dt><dd>{data.firmware_type || '—'}</dd></div><div><dt>Версія прошивки</dt><dd>{data.firmware_version || '—'}</dd></div></dl><h2>Примітки</h2><p className="description-text">{data.notes || 'Приміток немає.'}</p></section>
      <section className="form-panel form-stack"><h2>Нова версія на основі цієї</h2><p className="page-description">Копія отримує нову версію і власний склад компонентів. Використовуйте її, коли потрібно змінити конфігурацію після початку випробувань.</p><div className="form-actions"><Input aria-label="Нова версія сетапу" placeholder="Нова версія" maxLength={255} value={newVersion} onChange={e => setNewVersion(e.target.value)} /><Button disabled={clone.isPending || !newVersion.trim()} onClick={() => clone.mutate(newVersion.trim())}>Створити копію</Button></div></section></>}
    {tab === 'Компоненти' && <SetupBom setupId={id} />}{tab === 'Прошивка' && <SetupFirmware setup={data} />}
    {tab === 'Випробування' && <TestsPage setupId={id} />}{tab === 'Польоти' && <TestsPage setupId={id} flightOnly />}
    {tab === 'Файли' && <FilesPanel owner={{ kind: 'setup', id }} />}{tab === 'Коментарі' && <CommentsPanel owner={{ kind: 'setup', id }} />}
  </>
}

