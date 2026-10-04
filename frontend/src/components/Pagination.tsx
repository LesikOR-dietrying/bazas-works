import { Button } from './ui/button'

export function Pagination({ page, total, pageSize, onChange }: {
  page: number; total: number; pageSize: number; onChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  return <div className="pagination"><span>Усього: {total} · Сторінка {page} із {pages}</span>
    <Button variant="outline" disabled={page <= 1} onClick={() => onChange(page - 1)}>Назад</Button>
    <Button variant="outline" disabled={page >= pages} onClick={() => onChange(page + 1)}>Далі</Button></div>
}
