import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { ScanLine } from 'lucide-react'
import { api } from '../api/client'
import { ErrorNotice, Loading } from '../components/Feedback'
import { StatusBadge } from '../components/StatusBadge'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import type { ProductionItem, WorkItem } from '../features/production/types'

export function MyWorkPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [scanError, setScanError] = useState<unknown>()
  const work = useQuery({ queryKey: ['my-work'], queryFn: ({ signal }) => api<WorkItem[]>('/production/my-work', { signal }), refetchInterval: 15_000 })
  async function scan() {
    try {
      setScanError(undefined)
      const item = await api<ProductionItem>(`/production/scan/${encodeURIComponent(code.trim())}`)
      navigate(`/my-work/items/${item.id}`)
    } catch (error) { setScanError(error) }
  }
  return <><div className="page-heading"><div><p className="eyebrow">ВИРОБНИЧЕ РОБОЧЕ МІСЦЕ</p><h1>My Work</h1><p className="page-description">Ваші призначені операції та доступна робота відповідно до професійної ролі.</p></div></div>
    <form className="scan-panel" onSubmit={e => { e.preventDefault(); void scan() }}><ScanLine size={28} /><Input aria-label="Код виробу або партії" placeholder="Відскануйте QR або введіть код" value={code} onChange={e => setCode(e.target.value)} /><Button disabled={!code.trim()}>Відкрити</Button></form><ErrorNotice error={scanError || work.error} />
    {work.isPending && <Loading />}{work.data && <section className="work-grid">{work.data.map(row => <Link className="work-card" to={`/my-work/items/${row.item.id}`} key={row.execution.id}><div><span className="tracking-pill">{row.item.tracking_mode}</span><StatusBadge value={row.execution.status} /></div><h2>{row.item.identifier}</h2><p>{row.item.product_name} · {row.item.revision_code}</p><strong>{row.execution.stage_name}</strong><span>{row.execution.completed_quantity} / {row.execution.planned_quantity}</span></Link>)}{!work.data.length && <div className="empty-state"><h2>Активних операцій немає</h2><p>Нові роботи з’являться після запуску замовлення або завершення попереднього етапу.</p></div>}</section>}
  </>
}
