import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, apiBlob, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { ownerField } from './types'
import type { Attachment, FileOwner } from './types'

function sizeLabel(size: number) { return size < 1024 ? `${size} Б` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} КБ` : `${(size / (1024 * 1024)).toFixed(1)} МБ` }

export function FilesPanel({ owner }: { owner: FileOwner }) {
  const { data: user } = useSession(), cache = useQueryClient(), [page, setPage] = useState(1), [file, setFile] = useState<File | null>(null), [inputKey, setInputKey] = useState(0)
  const ownerKey = ownerField(owner), params = new URLSearchParams({ [ownerKey]: owner.id, page: String(page) })
  const files = useQuery({ queryKey: ['files', ownerKey, owner.id, page], queryFn: ({ signal }) => api<Page<Attachment>>(`/files?${params}`, { signal }) })
  const upload = useMutation({ mutationFn: (selected: File) => { const form = new FormData(); form.set('upload', selected); form.set(ownerKey, owner.id); return api<Attachment>('/files', { method: 'POST', body: form }) }, onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['files', ownerKey, owner.id] }); setPage(1); setFile(null); setInputKey(current => current + 1) } })
  const remove = useMutation({ mutationFn: (id: string) => send(`/files/${id}`, 'DELETE'), onSuccess: async () => { await cache.invalidateQueries({ queryKey: ['files', ownerKey, owner.id] }) } })
  const download = useMutation({ mutationFn: (item: Attachment) => apiBlob(`/files/${item.id}/download`), onSuccess: (blob, item) => { const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = item.original_filename.replace(/.*[\\/]/, '') || 'file'; document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 0) } })
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (file) upload.mutate(file) }
  function canRemove(item: Attachment) { return item.uploaded_by_id === user?.id || hasCapability(user, 'MANAGE_ALL_FILES') }
  return <section className="form-panel"><h2>Файли</h2><ErrorNotice error={files.error || upload.error || remove.error || download.error} />{files.isPending && <Loading />}{files.data && <><div className="table-scroll"><table><thead><tr><th>Файл</th><th>Розмір</th><th>Завантажив</th><th>Дата</th><th>Дії</th></tr></thead><tbody>{files.data.items.map(item => <tr key={item.id}><td>{item.original_filename}</td><td>{sizeLabel(item.size)}</td><td>{item.uploaded_by_name}</td><td>{new Date(item.created_at).toLocaleString('uk-UA')}</td><td><div className="form-actions"><Button variant="outline" disabled={download.isPending} onClick={() => download.mutate(item)}>Завантажити</Button>{canRemove(item) && <Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm(`Видалити файл «${item.original_filename}»? Цю дію неможливо скасувати.`)) remove.mutate(item.id) }}>Видалити</Button>}</div></td></tr>)}{!files.data.items.length && <tr><td colSpan={5}>Файлів ще немає.</td></tr>}</tbody></table></div><Pagination page={page} total={files.data.total} pageSize={files.data.page_size} onChange={setPage} /></>}
    <form className="form-stack" onSubmit={submit}><h2>Додати файл</h2><Input key={inputKey} aria-label="Оберіть файл" type="file" onChange={event => setFile(event.target.files?.[0] ?? null)} /><Button type="submit" disabled={!file || upload.isPending}>Завантажити файл</Button></form>
  </section>
}


