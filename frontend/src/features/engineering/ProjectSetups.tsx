import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { canEditEngineering, canManageProjectLinks, useSetupOptions } from './hooks'
import type { SetupOption } from './types'

export function ProjectSetups({ projectId }: { projectId: string }) {
  const { data: user } = useSession(), cache = useQueryClient(), [selected, setSelected] = useState('')
  const linked = useQuery({ queryKey: ['project-setups', projectId], enabled: canEditEngineering(user), queryFn: ({ signal }) => api<SetupOption[]>(`/projects/${projectId}/setups`, { signal }) })
  const options = useSetupOptions(canManageProjectLinks(user))
  const link = useMutation({ mutationFn: (setupId: string) => send<SetupOption>(`/projects/${projectId}/setups`, 'POST', { setup_id: setupId }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['project-setups', projectId] }); await cache.invalidateQueries({ queryKey: ['setups'] }); setSelected('') } })
  const unlink = useMutation({ mutationFn: (setupId: string) => send(`/projects/${projectId}/setups/${setupId}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['project-setups', projectId] }); await cache.invalidateQueries({ queryKey: ['setups'] }) } })
  if (!canEditEngineering(user)) return <ErrorNotice error={new Error('Конфігурації доступні інженерам, менеджерам та адміністраторам.')} />
  const available = options.data?.filter(setup => !linked.data?.some(item => item.id === setup.id)) ?? []
  return <section className="form-panel"><h2>Сетапи проєкту</h2><p className="page-description">Один сетап можна використати в кількох проєктах.</p><ErrorNotice error={linked.error || options.error || link.error || unlink.error} />{linked.isPending && <Loading />}
    {linked.data && <div className="table-scroll"><table><thead><tr><th>Сетап</th><th>Версія</th><th>Статус</th>{canManageProjectLinks(user) && <th>Дії</th>}</tr></thead><tbody>{linked.data.map(item => <tr key={item.id}><td><Link className="record-link" to={`/setups/${item.id}`}>{item.name}</Link></td><td>{item.version}</td><td><StatusBadge value={item.status} /></td>{canManageProjectLinks(user) && <td><Button variant="destructive" disabled={unlink.isPending} onClick={() => { if (window.confirm(`Відв’язати сетап «${item.name} · ${item.version}» від проєкту?`)) unlink.mutate(item.id) }}>Відв’язати</Button></td>}</tr>)}{!linked.data.length && <tr><td colSpan={canManageProjectLinks(user) ? 4 : 3}>Сетапів ще немає.</td></tr>}</tbody></table></div>}
    {canManageProjectLinks(user) && <div className="form-stack"><h2>Прив’язати сетап</h2><div className="form-actions"><select aria-label="Сетап для проєкту" className="form-input" value={selected} onChange={e => setSelected(e.target.value)}><option value="">Оберіть сетап</option>{available.map(item => <option key={item.id} value={item.id}>{item.name} · {item.version}</option>)}</select><Button disabled={!selected || link.isPending || options.isPending || options.isError} onClick={() => link.mutate(selected)}>Прив’язати</Button><Button asChild variant="outline"><Link to="/setups/new">Новий сетап</Link></Button></div></div>}
  </section>
}

