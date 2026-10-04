import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, send } from '../../api/client'
import type { Page } from '../../api/client'
import { ErrorNotice, Loading } from '../../components/Feedback'
import { Pagination } from '../../components/Pagination'
import { Button } from '../../components/ui/button'
import { useSession } from '../auth/useSession'
import { hasCapability } from '../auth/types'
import { ownerField } from './types'
import type { Comment, CommentOwner } from './types'

export function CommentsPanel({ owner }: { owner: CommentOwner }) {
  const { data: user } = useSession(), cache = useQueryClient(), [page, setPage] = useState(1)
  const [draft, setDraft] = useState(''), [editing, setEditing] = useState<Comment | null>(null), [editText, setEditText] = useState('')
  const ownerKey = ownerField(owner), params = new URLSearchParams({ [ownerKey]: owner.id, page: String(page) })
  const comments = useQuery({ queryKey: ['comments', ownerKey, owner.id, page], queryFn: ({ signal }) => api<Page<Comment>>(`/comments?${params}`, { signal }) })
  const invalidate = () => cache.invalidateQueries({ queryKey: ['comments', ownerKey, owner.id] })
  const create = useMutation({ mutationFn: (text: string) => send<Comment>('/comments', 'POST', { [ownerKey]: owner.id, text }), onSuccess: async () => { await invalidate(); setDraft(''); setPage(1) } })
  const update = useMutation({ mutationFn: ({ id, text }: { id: string; text: string }) => send<Comment>(`/comments/${id}`, 'PATCH', { text }), onSuccess: async () => { await invalidate(); setEditing(null); setEditText('') } })
  const remove = useMutation({ mutationFn: (id: string) => send(`/comments/${id}`, 'DELETE'), onSuccess: async () => { await invalidate() } })
  function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (draft.trim()) create.mutate(draft.trim()) }
  function canManage(comment: Comment) { return comment.author_id === user?.id || hasCapability(user, 'MANAGE_ALL_FILES') }
  return <section className="form-panel"><h2>Коментарі</h2><ErrorNotice error={comments.error || create.error || update.error || remove.error} />{comments.isPending && <Loading />}
    {comments.data && <><div className="comment-list">{comments.data.items.map(comment => <article className="comment-card" key={comment.id}><div className="comment-header"><strong>{comment.author_name}</strong><time dateTime={comment.created_at}>{new Date(comment.created_at).toLocaleString('uk-UA')}</time>{comment.updated_at !== comment.created_at && <span>змінено</span>}</div>{editing?.id === comment.id ? <form className="form-stack" onSubmit={event => { event.preventDefault(); if (editText.trim()) update.mutate({ id: comment.id, text: editText.trim() }) }}><textarea aria-label="Редагувати коментар" className="form-input" required value={editText} onChange={event => setEditText(event.target.value)} /><div className="form-actions"><Button type="submit" disabled={update.isPending || !editText.trim()}>Зберегти</Button><Button type="button" variant="outline" onClick={() => setEditing(null)}>Скасувати</Button></div></form> : <p className="description-text">{comment.text}</p>}{canManage(comment) && editing?.id !== comment.id && <div className="form-actions"><Button variant="outline" onClick={() => { setEditing(comment); setEditText(comment.text) }}>Редагувати</Button><Button variant="destructive" disabled={remove.isPending} onClick={() => { if (window.confirm('Видалити коментар? Цю дію неможливо скасувати.')) remove.mutate(comment.id) }}>Видалити</Button></div>}</article>)}{!comments.data.items.length && <p>Коментарів ще немає.</p>}</div><Pagination page={page} total={comments.data.total} pageSize={comments.data.page_size} onChange={setPage} /></>}
    <form className="form-stack" onSubmit={submit}><h2>Новий коментар</h2><textarea aria-label="Текст коментаря" className="form-input" required value={draft} onChange={event => setDraft(event.target.value)} /><Button type="submit" disabled={create.isPending || !draft.trim()}>Додати коментар</Button></form>
  </section>
}


