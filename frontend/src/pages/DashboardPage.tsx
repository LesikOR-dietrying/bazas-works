import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle, ArrowUpRight, CheckCircle2, CircleDot, Clock3, FlaskConical,
  FolderKanban, ListChecks, Package, Wrench,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { ErrorNotice, Loading } from '../components/Feedback'
import { StatusBadge } from '../components/StatusBadge'
import { hasCapability } from '../features/auth/types'
import { useSession } from '../features/auth/useSession'
import { SystemStatus } from '../features/system/SystemStatus'
import type { TaskSummary } from '../features/tasks/types'
import { labelForCode } from '../lib/labels'

interface DashboardProject { id: string; name: string; status: string; responsible_name: string }
interface DashboardSetup { id: string; name: string; version: string; status: string; updated_at: string }
interface DashboardTest { id: string; name: string; test_type: string; status: string; test_date: string | null }
interface DashboardProblem { type: string; id: string; title: string; status: string; path: string }
interface DashboardData { my_tasks: TaskSummary; active_projects: DashboardProject[]; blocked_tasks: DashboardProblem[]; engineering: { development_setups: DashboardSetup[]; ready_setups: DashboardSetup[]; recent_tests: DashboardTest[]; failed_tests: DashboardProblem[] } | null }

function PanelHeading({ eyebrow, title, link, linkLabel }: { eyebrow: string; title: string; link?: string; linkLabel?: string }) {
  return <div className="dashboard-panel-heading"><div><span>{eyebrow}</span><h2>{title}</h2></div>{link && <Link to={link}>{linkLabel}<ArrowUpRight size={15} /></Link>}</div>
}

function MetricCard({ label, value, hint, icon: Icon, tone }: { label: string; value: number; hint: string; icon: LucideIcon; tone: string }) {
  return <Link to="/tasks" className={`dashboard-metric metric-${tone}`} aria-label={`${label}: ${value}`}><span className="metric-icon"><Icon size={18} /></span><div><strong>{value}</strong><span>{label}</span><small>{hint}</small></div><ArrowUpRight className="metric-arrow" size={16} /></Link>
}

function ProblemList({ title, items, empty }: { title: string; items: DashboardProblem[]; empty: string }) {
  return <section className="dashboard-panel dashboard-problems"><PanelHeading eyebrow="ПОТРЕБУЄ УВАГИ" title={title} />{items.length ? <div className="dashboard-list">{items.map(item => <Link className="dashboard-list-row" to={item.path} key={`${item.type}-${item.id}`}><span className="list-indicator danger" /><strong>{item.title}</strong><StatusBadge value={item.status} /><ArrowUpRight size={14} /></Link>)}</div> : <div className="dashboard-clear"><CheckCircle2 size={20} /><span>{empty}</span></div>}</section>
}

function SetupList({ title, items, tone }: { title: string; items: DashboardSetup[]; tone: 'development' | 'ready' }) {
  return <section className="dashboard-panel"><PanelHeading eyebrow={tone === 'ready' ? 'ГОТОВО' : 'У РОЗРОБЦІ'} title={title} link="/setups" linkLabel="Усі" />{items.length ? <div className="dashboard-list">{items.map(item => <Link className="dashboard-list-row" to={`/setups/${item.id}`} key={item.id}><span className={`list-indicator ${tone}`} /><div className="list-copy"><strong>{item.name}</strong><small>Версія {item.version} · {new Date(item.updated_at).toLocaleDateString('uk-UA')}</small></div><StatusBadge value={item.status} /><ArrowUpRight size={14} /></Link>)}</div> : <div className="dashboard-empty">Сетапів у цьому стані немає.</div>}</section>
}

export function DashboardPage() {
  const dashboard = useQuery({ queryKey: ['dashboard'], queryFn: ({ signal }) => api<DashboardData>('/dashboard', { signal }) })
  const { data: user } = useSession()
  const today = new Intl.DateTimeFormat('uk-UA', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
  const quickLinks = [
    { path: '/tasks', label: 'Мої задачі', icon: ListChecks, visible: true },
    { path: '/rnd', label: 'Розробка', icon: FlaskConical, visible: true },
    { path: '/products', label: 'Продукція', icon: Package, visible: hasCapability(user, 'VIEW_ENGINEERING') },
    { path: '/production', label: 'Виробництво', icon: Wrench, visible: hasCapability(user, 'VIEW_PRODUCTION') },
  ].filter(item => item.visible)

  return <div className="dashboard-page">
    <header className="dashboard-hero-heading"><div><p className="eyebrow">ОГЛЯД РОБОТИ</p><h1>Вітаємо, {user?.full_name?.split(' ')[0] || 'колего'}</h1><p className="page-description">{today.charAt(0).toUpperCase() + today.slice(1)}. Тут зібрано роботу, яка потребує вашої уваги.</p></div><nav className="dashboard-quick-links" aria-label="Швидкі переходи">{quickLinks.map(({ path, label, icon: Icon }) => <Link key={path} to={path}><Icon size={16} /><span>{label}</span></Link>)}</nav></header>

    <ErrorNotice error={dashboard.error} />
    {dashboard.isPending && <Loading />}
    {dashboard.data && <>
      <section className="dashboard-focus" aria-label="Фокус дня"><div className="focus-copy"><span className="focus-label"><CircleDot size={13} /> ФОКУС ДНЯ</span><h2>{dashboard.data.my_tasks.active ? `${dashboard.data.my_tasks.active} активних задач у роботі` : 'Активних задач немає'}</h2><p>{dashboard.data.my_tasks.overdue ? `${dashboard.data.my_tasks.overdue} прострочених задач потребують рішення.` : 'Прострочених задач немає — план виконується вчасно.'}</p><Link to="/tasks">Відкрити мої задачі <ArrowUpRight size={16} /></Link></div><div className="focus-progress"><div className="focus-progress-value"><strong>{dashboard.data.my_tasks.total ? Math.round(dashboard.data.my_tasks.completed / dashboard.data.my_tasks.total * 100) : 0}%</strong><span>виконано</span></div><progress max={dashboard.data.my_tasks.total || 1} value={dashboard.data.my_tasks.completed} /><small>{dashboard.data.my_tasks.completed} із {dashboard.data.my_tasks.total} задач завершено</small></div></section>

      <section aria-label="Мої задачі" className="dashboard-metrics">
        <MetricCard label="Активні задачі" value={dashboard.data.my_tasks.active} hint="Зараз у роботі" icon={CircleDot} tone="active" />
        <MetricCard label="Прострочені" value={dashboard.data.my_tasks.overdue} hint="Поза плановим строком" icon={Clock3} tone="overdue" />
        <MetricCard label="Заблоковані" value={dashboard.data.my_tasks.blocked} hint="Очікують рішення" icon={AlertTriangle} tone="blocked" />
        <MetricCard label="Завершені за 7 днів" value={dashboard.data.my_tasks.completed_recently} hint="Останній тиждень" icon={CheckCircle2} tone="done" />
      </section>

      <div className="dashboard-primary-grid">
        <section className="dashboard-panel dashboard-projects"><PanelHeading eyebrow="ПРОЄКТИ РОЗРОБКИ" title="Активні проєкти" link="/projects" linkLabel="Усі проєкти" />{dashboard.data.active_projects.length ? <div className="project-overview-list">{dashboard.data.active_projects.map((item, index) => <Link to={`/projects/${item.id}`} className="project-overview-row" key={item.id}><span className="project-index">{String(index + 1).padStart(2, '0')}</span><div><strong>{item.name}</strong><small>Відповідальний: {item.responsible_name}</small></div><StatusBadge value={item.status} /><ArrowUpRight size={15} /></Link>)}</div> : <div className="dashboard-empty"><FolderKanban size={22} /><span>Активних доступних проєктів немає.</span></div>}</section>
        <ProblemList title="Заблоковані задачі" items={dashboard.data.blocked_tasks} empty="Заблокованих задач немає." />
      </div>

      {dashboard.data.engineering && <section className="dashboard-engineering"><div className="dashboard-section-title"><div><span>СТАН РОЗРОБКИ</span><h2>Стан розробки</h2></div><p>Конфігурації та останні результати випробувань</p></div><div className="dashboard-engineering-grid"><SetupList title="У розробці" items={dashboard.data.engineering.development_setups} tone="development" /><SetupList title="Готові конфігурації" items={dashboard.data.engineering.ready_setups} tone="ready" /><section className="dashboard-panel dashboard-tests"><PanelHeading eyebrow="РЕЗУЛЬТАТИ ВИПРОБУВАНЬ" title="Останні випробування" link="/tests" linkLabel="Усі" />{dashboard.data.engineering.recent_tests.length ? <div className="dashboard-list">{dashboard.data.engineering.recent_tests.map(item => <Link className="dashboard-list-row" to={`/tests/${item.id}`} key={item.id}><span className="list-indicator test" /><div className="list-copy"><strong>{item.name}</strong><small>{labelForCode(item.test_type)} · {item.test_date ? new Date(item.test_date).toLocaleDateString('uk-UA') : 'Заплановано'}</small></div><StatusBadge value={item.status} /><ArrowUpRight size={14} /></Link>)}</div> : <div className="dashboard-empty">Випробувань ще немає.</div>}</section><ProblemList title="Невдалі випробування" items={dashboard.data.engineering.failed_tests} empty="Невдалих випробувань немає." /></div></section>}
    </>}
    <SystemStatus />
  </div>
}
