import { Link } from 'react-router-dom'
import { ArrowRight, Boxes, ClipboardCheck, GitBranch, Microscope } from 'lucide-react'
import { useSession } from '../features/auth/useSession'
import { hasCapability } from '../features/auth/types'
import { ProjectsPage } from '../features/projects/ProjectsPage'

const sections = [
  { path: '/projects', title: 'Проєкти', description: 'Команда, гілки, задачі та рішення.', meta: 'R&D CONTROL', icon: GitBranch },
  { path: '/setups', title: 'Конфігурації', description: 'Експериментальні сетапи, BOM і прошивки.', meta: 'CONFIGURATIONS', icon: ClipboardCheck },
  { path: '/components', title: 'Компоненти', description: 'Каталог і технічні характеристики.', meta: 'ENGINEERING LIBRARY', icon: Boxes },
  { path: '/tests', title: 'Випробування', description: 'Плани, вимірювання, докази й висновки.', meta: 'EVIDENCE', icon: Microscope },
] as const

export function RndPage() {
  const { data: user } = useSession()
  const visible = hasCapability(user, 'VIEW_ENGINEERING') ? sections : sections.slice(0, 1)
  return <div className="rnd-workspace"><div className="page-heading rnd-heading"><div><p className="eyebrow">ENGINEERING WORKSPACE</p><h1>Дослідження та розробка</h1><p className="page-description">Керуйте інженерними рішеннями від першої гіпотези до перевіреної конфігурації, готової стати ревізією продукту.</p></div><span className="module-mark">R&D <small>01</small></span></div>
    <section className="rnd-flow" aria-label="Процес дослідження та розробки">
      {['Проєкт', 'Гілка', 'Конфігурація', 'Докази'].map((step, index) => <div className="rnd-flow-step" key={step}><span>{String(index + 1).padStart(2, '0')}</span><strong>{step}</strong>{index < 3 && <ArrowRight size={16} aria-hidden="true" />}</div>)}
    </section>
    <div className="rnd-module-grid">{visible.slice(1).map(({ path, title, description, meta, icon: Icon }) => <Link key={path} to={path} className="rnd-module-card"><div className="rnd-card-top"><span className="rnd-module-icon"><Icon size={21} strokeWidth={1.7} /></span><ArrowRight className="rnd-card-arrow" size={18} /></div><span className="rnd-card-meta">{meta}</span><h2>{title}</h2><p>{description}</p></Link>)}</div>
    <section className="rnd-projects"><ProjectsPage embedded /></section>
  </div>
}
