import { useSession } from '../auth/useSession'

export function SettingsPage() {
  const { data: user } = useSession()
  return <><div className="page-heading"><h1>Налаштування</h1></div><section className="form-panel"><h2>Обліковий запис адміністратора</h2><p>{user?.full_name} · {user?.username}{user?.email ? ` · ${user.email}` : ''}</p>
    <p className="page-description">Керування обліковими записами доступне в розділі «Користувачі».</p><p className="todo-label">ЗАПЛАНОВАНО · Розширені налаштування системи — наступні етапи.</p></section></>
}
