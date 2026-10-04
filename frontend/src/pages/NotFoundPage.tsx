import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return <section className="empty-state"><p className="eyebrow">404</p><h1>Сторінку не знайдено</h1><p>Перевірте адресу або поверніться до робочого простору.</p><Link to="/" className="primary-link">На головну</Link></section>
}
