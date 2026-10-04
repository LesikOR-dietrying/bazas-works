import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import type { FirmwareRevision, Setup } from './types'
import { FilesPanel } from '../collaboration/FilesPanel'

function RevisionDetails({ revision }: { revision: FirmwareRevision }) {
  const [open, setOpen] = useState(false)
  return <details className="firmware-details" onToggle={event => setOpen(event.currentTarget.open)}><summary>{revision.version_name} · деталі</summary><p className="description-text">{revision.description || 'Без опису'}</p><pre>{revision.config_text || 'Текст конфігурації не додано.'}</pre>{open && <FilesPanel owner={{ kind: 'firmware_revision', id: revision.id }} />}</details>
}

export function SetupFirmware({ setup }: { setup: Setup }) {
  const [page, setPage] = useState(1), [versionName, setVersionName] = useState(''), [firmwareType, setFirmwareType] = useState(setup.firmware_type)
  const [firmwareVersion, setFirmwareVersion] = useState(setup.firmware_version), [description, setDescription] = useState(''), [configText, setConfigText] = useState('')
  const cache = useQueryClient()
  const revisions = useQuery({ queryKey: ['firmware', setup.id, page], queryFn: ({ signal }) => api<Page<FirmwareRevision>>(`/firmware?setup_id=${setup.id}&page=${page}`, { signal }) })
  const create = useMutation({ mutationFn: () => send<FirmwareRevision>('/firmware', 'POST', { setup_id: setup.id, version_name: versionName.trim(), firmware_type: firmwareType.trim(), firmware_version: firmwareVersion.trim(), description, config_text: configText }), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['firmware', setup.id] }); setPage(1); setVersionName(''); setDescription(''); setConfigText('') } })
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (versionName.trim() && firmwareType.trim() && firmwareVersion.trim()) create.mutate() }
  return <><section className="form-panel"><h2>Ревізії прошивки</h2><p className="page-description">Кожна ревізія належить цьому сетапу. Для змін створюйте нову ревізію; записи зберігають історію випробувань.</p><ErrorNotice error={revisions.error} />{revisions.isPending && <Loading />}{revisions.data && <><div className="table-scroll"><table><thead><tr><th>Ревізія</th><th>Тип</th><th>Версія прошивки</th><th>Створено</th></tr></thead><tbody>{revisions.data.items.map(item => <tr key={item.id}><td>{item.version_name}</td><td>{item.firmware_type}</td><td>{item.firmware_version}</td><td>{new Date(item.created_at).toLocaleString('uk-UA')}</td></tr>)}{!revisions.data.items.length && <tr><td colSpan={4}>Ревізій ще немає.</td></tr>}</tbody></table></div><Pagination page={page} total={revisions.data.total} pageSize={revisions.data.page_size} onChange={setPage} />{revisions.data.items.map(item => <RevisionDetails revision={item} key={item.id} />)}</>}</section>
    <form className="form-panel form-stack" onSubmit={submit}><h2>Нова ревізія</h2><div className="editor-grid"><Field label="Назва ревізії"><Input required maxLength={255} value={versionName} onChange={e => setVersionName(e.target.value)} /></Field><Field label="Тип прошивки"><Input required maxLength={255} value={firmwareType} onChange={e => setFirmwareType(e.target.value)} /></Field><Field label="Версія прошивки"><Input required maxLength={255} value={firmwareVersion} onChange={e => setFirmwareVersion(e.target.value)} /></Field></div><Field label="Опис"><textarea className="form-input" value={description} onChange={e => setDescription(e.target.value)} /></Field><Field label="Текст конфігурації"><textarea className="form-input" value={configText} onChange={e => setConfigText(e.target.value)} /></Field><ErrorNotice error={create.error} /><Button type="submit" disabled={create.isPending}>Створити ревізію</Button></form>
  </>
}
