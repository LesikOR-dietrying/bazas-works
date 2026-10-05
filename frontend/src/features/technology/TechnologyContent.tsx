import { useEffect, useState } from 'react'
import { apiBlob, ApiError } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Button } from '../../components/ui/button'
import type { ChecklistItem, TechnologyBlock } from '../products/types'

function textValue(value: unknown): string { return typeof value === 'string' ? value : '' }

function ProtectedAttachment({ id, kind, label }: { id: string; kind: 'image' | 'video' | 'file'; label: string }) {
  const [url, setUrl] = useState(''), [error, setError] = useState<unknown>(), [loading, setLoading] = useState(true)
  useEffect(() => {
    let active = true, objectUrl = ''
    void apiBlob(`/files/${id}/content`).then(blob => {
      if (!active) return
      objectUrl = URL.createObjectURL(blob); setUrl(objectUrl); setLoading(false)
    }).catch(reason => { if (active) { setError(reason); setLoading(false) } })
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [id])
  if (loading) return <Loading />
  if (error) {
    const message = error instanceof ApiError && error.status === 404 ? 'Файл не знайдено.' : error instanceof ApiError && error.status === 403 ? 'У вас немає доступу до цього файлу.' : error
    return <ErrorNotice error={typeof message === 'string' ? new Error(message) : message} />
  }
  if (kind === 'image') return <img className="technology-image" src={url} alt={label} />
  if (kind === 'video') return <video className="technology-video" src={url} controls />
  return <Button variant="outline" onClick={() => { const anchor = document.createElement('a'); anchor.href = url; anchor.download = label || 'file'; anchor.click() }}>Завантажити файл</Button>
}

export function TechnologyContent({ block, checklist = [] }: { block: TechnologyBlock; checklist?: ChecklistItem[] }) {
  const text = textValue(block.payload.text), label = textValue(block.payload.label) || textValue(block.payload.filename) || 'Вкладення'
  if (block.block_type === 'TEXT') return <div className="content-block block-text">{text || 'Текст не заповнено.'}</div>
  if (block.block_type === 'WARNING') return <div className="content-block block-warning" role="note"><strong>Увага</strong><p>{text || 'Попередження не заповнено.'}</p></div>
  if (block.block_type === 'CHECKLIST') return <div className="content-block block-checklist"><strong>{text || 'Чекліст'}</strong><ul className="checklist-preview">{checklist.filter(item => item.block_id === block.id).map(item => <li key={item.id}><input type="checkbox" disabled /> {item.text}{item.required ? ' *' : ''}</li>)}</ul></div>
  if (block.block_type === 'MEASUREMENT') return <div className="content-block block-measurement"><strong>{label || 'Вимірювання'}</strong><p>{textValue(block.payload.expected) || 'Значення задає виконавець'} {textValue(block.payload.unit)}</p></div>
  if (!block.attachment_id) return <div className="content-block"><ErrorNotice error={new Error('До блоку не прикріплено файл.')} /></div>
  if (block.block_type === 'ANNOTATED_IMAGE' && block.annotation_version !== 1) return <div className="content-block"><ErrorNotice error={new Error(`Формат анотації версії ${block.annotation_version} поки не підтримується.`)} /></div>
  if (block.block_type === 'IMAGE' || block.block_type === 'ANNOTATED_IMAGE') return <figure className="content-block"><ProtectedAttachment id={block.attachment_id} kind="image" label={label} />{label && <figcaption>{label}</figcaption>}{block.block_type === 'ANNOTATED_IMAGE' && Object.keys(block.annotation_source).length > 0 && <p className="page-description">Анотацію збережено у форматі версії {block.annotation_version}.</p>}</figure>
  if (block.block_type === 'VIDEO') return <div className="content-block"><ProtectedAttachment id={block.attachment_id} kind="video" label={label} /></div>
  return <div className="content-block"><p>{label}</p><ProtectedAttachment id={block.attachment_id} kind="file" label={label} /></div>
}
