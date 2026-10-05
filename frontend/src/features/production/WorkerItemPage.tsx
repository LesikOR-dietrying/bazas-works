import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, apiBlob, send } from '../../api/client'
import { ErrorNotice, Field, Loading } from '../../components/Feedback'
import { StatusBadge } from '../../components/StatusBadge'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import type { ExecutionDetail, StageExecution } from './types'
import { labelForCode } from '../../lib/labels'
import { TechnologyContent } from '../technology/TechnologyContent'

interface Answer { checked: boolean; note: string; photo_attachment_id: string | null }
interface Attachment { id: string }

export function WorkerItemPage() {
  const { id = '' } = useParams(), navigate = useNavigate(), cache = useQueryClient()
  const detail = useQuery({ queryKey: ['production-item', id], queryFn: ({ signal }) => api<ExecutionDetail>(`/production/items/${id}`, { signal }) })
  const [answers, setAnswers] = useState<Record<string, Answer>>({})
  const [quantity, setQuantity] = useState(''), [note, setNote] = useState('')
  const start = useMutation({ mutationFn: (executionId: string) => send<StageExecution>(`/production/executions/${executionId}/start`, 'POST'), onSuccess: async () => cache.invalidateQueries({ queryKey: ['production-item', id] }) })
  const complete = useMutation({ mutationFn: (data: ExecutionDetail) => send<StageExecution>(`/production/executions/${data.execution.id}/complete`, 'POST', { quantity: data.item.tracking_mode === 'QUANTITY' ? Number(quantity || data.execution.planned_quantity - data.execution.completed_quantity) : null, result_note: note, idempotency_key: crypto.randomUUID(), checklist: data.checklist.map(item => ({ template_item_id: item.id, ...(answers[item.id] ?? { checked: false, note: '', photo_attachment_id: null }) })) }), onSuccess: async result => { await Promise.all([cache.invalidateQueries({ queryKey: ['my-work'] }), cache.invalidateQueries({ queryKey: ['production-item', id] })]); if (result.status === 'PASSED') navigate('/my-work') } })
  async function upload(executionId: string, checklistId: string, file: File) {
    const body = new FormData(); body.append('upload', file); body.append('stage_execution_id', executionId)
    const attachment = await api<Attachment>('/files', { method: 'POST', body })
    setAnswers(current => ({ ...current, [checklistId]: { ...(current[checklistId] ?? { checked: false, note: '' }), photo_attachment_id: attachment.id } }))
  }
  async function download(id: string, name: string) {
    const blob = await apiBlob(`/files/${id}/download`), url = URL.createObjectURL(blob)
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url)
  }
  if (detail.isPending) return <Loading />
  if (!detail.data) return <ErrorNotice error={detail.error} />
  const data = detail.data, execution = data.execution
  return <><Link className="back-link" to="/my-work">← До моєї роботи</Link><div className="worker-header"><div><span className="tracking-pill">{labelForCode(data.item.tracking_mode)}</span><h1>{data.item.identifier}</h1><p>{data.item.product_name} · {data.item.revision_code} · {data.item.order_number}</p></div><StatusBadge value={execution.status} /></div>
    <section className="current-stage"><p className="eyebrow">ПОТОЧНИЙ ЕТАП</p><h2>{execution.stage_name}</h2><p>{data.instructions}</p>{data.operation_name && <h3>{data.operation_name}</h3>}{data.blocks.map(block => <TechnologyContent key={block.id} block={block} checklist={data.checklist} />)}{data.firmware.length > 0 && <div className="firmware-for-worker"><h3>Прошивки для цієї версії</h3>{data.firmware.map(item => <article key={`${item.artifact_name}-${item.release_version}-${item.purpose}`}><strong>{item.purpose}: {item.artifact_name} · {item.release_version}</strong><p>{item.description}</p><div className="form-actions">{item.binary_attachment_id && <Button variant="outline" onClick={() => void download(item.binary_attachment_id!, `${item.artifact_name}-${item.release_version}`)}>Завантажити прошивку</Button>}{item.config_attachment_id && <Button variant="outline" onClick={() => void download(item.config_attachment_id!, `${item.artifact_name}-${item.release_version}-config`)}>Завантажити конфігурацію</Button>}</div>{item.config_text && <pre>{item.config_text}</pre>}</article>)}</div>}{data.acceptance_criteria && <div className="acceptance"><strong>Критерій приймання</strong><p>{data.acceptance_criteria}</p></div>}</section>
    {execution.status === 'READY' && <Button className="worker-action" onClick={() => start.mutate(execution.id)} disabled={start.isPending}>Почати операцію</Button>}
    {execution.status === 'IN_PROGRESS' && <form className="worker-checklist" onSubmit={e => { e.preventDefault(); complete.mutate(data) }}><h2>Чекліст</h2>{data.checklist.map(item => { const answer = answers[item.id] ?? { checked: false, note: '', photo_attachment_id: null }; return <div className="worker-check" key={item.id}><label><input type="checkbox" checked={answer.checked} onChange={e => setAnswers(current => ({ ...current, [item.id]: { ...answer, checked: e.target.checked } }))} /><span>{item.text}{item.required && ' *'}</span></label>{item.note_required && <Input placeholder="Обов’язкова примітка" value={answer.note} onChange={e => setAnswers(current => ({ ...current, [item.id]: { ...answer, note: e.target.value } }))} />}{item.photo_required && <Field label={answer.photo_attachment_id ? 'Фото додано' : 'Додайте фото'}><Input type="file" accept="image/*" capture="environment" onChange={e => { const file = e.target.files?.[0]; if (file) void upload(execution.id, item.id, file) }} /></Field>}</div>})}{data.item.tracking_mode === 'QUANTITY' && <Field label="Виконана кількість"><Input type="number" min={1} max={execution.planned_quantity - execution.completed_quantity} value={quantity} onChange={e => setQuantity(e.target.value)} /></Field>}<Field label="Результат / примітка"><textarea className="form-input" value={note} onChange={e => setNote(e.target.value)} /></Field><ErrorNotice error={complete.error || start.error} /><Button type="submit" className="worker-action" disabled={complete.isPending}>Завершити етап</Button></form>}
  </>
}
