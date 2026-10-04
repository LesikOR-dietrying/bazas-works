import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { canEditEngineering, useComponent } from './hooks'
import { TestsPage } from '../tests/TestsPage'
import { FilesPanel } from '../collaboration/FilesPanel'
import type { Setup } from './types'

const specificationLabels: Record<string, string> = { kv: 'KV (об/хв/В)', voltage: 'Робоча напруга', max_current_a: 'Максимальний струм (А)', max_power_w: 'Максимальна потужність (Вт)', weight_g: 'Маса (г)', recommended_propellers: 'Рекомендовані пропелери', continuous_current_a: 'Постійний струм (А)', burst_current_a: 'Піковий струм (А)', firmware: 'Прошивка' }
function displayValue(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(item => String(item)).join(', ')
  return JSON.stringify(value) ?? '—'
}

export function ComponentDetail() {
  const { id = '' } = useParams(), { data: user } = useSession(), component = useComponent(id, canEditEngineering(user))
  const setups = useQuery({
    queryKey: ['setups', 'component', id],
    enabled: Boolean(id) && canEditEngineering(user),
    queryFn: ({ signal }) => api<Page<Setup>>(`/setups?component_id=${id}&sort=name&direction=asc&page_size=100`, { signal }),
  })
  const cache = useQueryClient(), navigate = useNavigate()
  const remove = useMutation({ mutationFn: () => send(`/components/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['components'] }); await cache.invalidateQueries({ queryKey: ['component-options'] }); navigate('/components') } })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Каталог компонентів доступний інженерам, менеджерам та адміністраторам.')} />
  if (component.isPending) return <Loading />
  if (!component.data) return <ErrorNotice error={component.error} />
  const data = component.data
  const setupItems = Array.isArray(setups.data?.items) ? setups.data.items : []
  return <><div className="page-heading"><div><Link className="back-link" to="/components">← Компоненти</Link><h1>{data.name}</h1></div><div className="form-actions"><Button asChild variant="outline"><Link to={`/components/${id}/edit`}>Редагувати</Link></Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити компонент «${data.name}»? Якщо він використовується в конфігураціях, сервер не дозволить видалення.`)) remove.mutate() }}>Видалити</Button></div></div>
    <ErrorNotice error={remove.error} /><section className="form-panel"><dl className="detail-grid"><div><dt>Категорія</dt><dd>{data.category}</dd></div><div><dt>Виробник</dt><dd>{data.manufacturer || '—'}</dd></div><div><dt>Модель</dt><dd>{data.model || '—'}</dd></div><div><dt>Оновлено</dt><dd>{new Date(data.updated_at).toLocaleString('uk-UA')}</dd></div></dl><h2>Опис</h2><p className="description-text">{data.description || 'Опис ще не додано.'}</p></section>
    <section className="form-panel"><h2>Характеристики</h2>{Object.entries(data.specifications).length ? <dl className="detail-grid">{Object.entries(data.specifications).map(([key, value]) => <div key={key}><dt>{specificationLabels[key] ?? key}</dt><dd>{displayValue(value)}</dd></div>)}</dl> : <p>Характеристик ще немає.</p>}</section>
    <section className="form-panel"><h2>Використання у сетапах</h2><ErrorNotice error={setups.error} />{setups.isPending ? <Loading /> : setupItems.length ? <div className="table-scroll"><table><thead><tr><th>Сетап</th><th>Версія</th><th>Статус</th></tr></thead><tbody>{setupItems.map(setup => <tr key={setup.id}><td><Link className="record-link" to={`/setups/${setup.id}`}>{setup.name}</Link></td><td>{setup.version}</td><td><StatusBadge value={setup.status} /></td></tr>)}</tbody></table></div> : <p>Компонент ще не використовується у сетапах.</p>}</section>
    <section className="form-panel"><h2>Документація та примітки</h2>{data.datasheet_url && <p><a className="record-link" href={data.datasheet_url} target="_blank" rel="noopener noreferrer">Відкрити datasheet ↗</a></p>}<p className="description-text">{data.notes || 'Приміток немає.'}</p></section>
    <TestsPage componentId={id} />
    <FilesPanel owner={{ kind: 'component', id }} />
  </>
}

