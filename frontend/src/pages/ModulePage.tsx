import { Construction } from 'lucide-react'

interface ModulePageProps {
  title: string
  description: string
  phase: number
}

export function ModulePage({ title, description, phase }: ModulePageProps) {
  return (
    <>
      <div className="page-heading"><div><p className="eyebrow">РОБОЧИЙ ПРОСТІР</p><h1>{title}</h1><p className="page-description">{description}</p></div></div>
      <section className="empty-state">
        <span className="empty-icon"><Construction size={30} /></span>
        <span className="phase-badge">ЗАПЛАНОВАНО · ЕТАП {phase}</span>
        <h2>Модуль ще не реалізовано</h2>
        <p>Цей розділ підготовлений для наступного етапу розробки.<br />Створення та перегляд записів будуть доступні після його реалізації.</p>
      </section>
    </>
  )
}
