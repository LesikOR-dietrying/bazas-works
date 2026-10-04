import { ChevronRight, Hexagon, LogOut, Search } from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { primaryNavigation, utilityNavigation, visibleNavigation } from '../app/navigation'
import { useSession } from '../features/auth/useSession'
import { replaceSession } from '../features/auth/sessionCache'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { send } from '../api/client'
import { Button } from './ui/button'
import { ErrorNotice } from './Feedback'
import { Input } from './ui/input'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { roleLabels } from '../features/auth/types'

export function Layout() {
  const { pathname } = useLocation()
  const { data: user } = useSession()
  const mainItems = visibleNavigation(primaryNavigation, user)
  const utilityItems = visibleNavigation(utilityNavigation, user)
  const current = [...mainItems, ...utilityItems].find(item => pathname === item.path || pathname.startsWith(`${item.path}/`))
  const cache = useQueryClient()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const logout = useMutation({ mutationFn: () => send('/auth/logout', 'POST'), onSuccess: () => replaceSession(cache, null) })
  function submitSearch(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (search.trim()) { navigate(`/search?q=${encodeURIComponent(search.trim())}`); setSearch('') } }

  return (
    <div className="app-shell horizontal-shell">
      <a href="#main" className="skip-link">Перейти до вмісту</a>
      <header className="application-header">
        <div className="application-header-main">
          <NavLink to="/" className="brand" aria-label="BAZA — головна"><span className="brand-symbol"><Hexagon size={25} strokeWidth={1.7} /></span><span>BAZA</span></NavLink>
          <nav aria-label="Основні розділи" className="primary-navigation">
            {mainItems.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} className={({ isActive }) => `primary-nav-item ${isActive ? 'active' : ''}`}><Icon size={17} aria-hidden="true" /><span>{label}</span></NavLink>)}
          </nav>
          <form role="search" className="top-search" onSubmit={submitSearch}><Search size={16} aria-hidden="true" /><Input aria-label="Глобальний пошук" value={search} onChange={event => setSearch(event.target.value)} placeholder="Пошук…" /><button className="search-submit" type="submit" aria-label="Знайти"><ChevronRight size={15} /></button></form>
          <div className="account-menu"><span className="user-avatar" aria-hidden="true">{user?.full_name?.charAt(0).toUpperCase()}</span><span className="user-copy"><strong>{user?.full_name}</strong><small>{user?.roles?.[0] ? roleLabels[user.roles[0]] : user?.role}</small></span><Button className="logout-button" variant="outline" aria-label="Вийти" title="Вийти" disabled={logout.isPending} onClick={() => logout.mutate()}><LogOut size={16} /></Button></div>
        </div>
        <div className="application-context-bar">
          <span className="breadcrumb"><NavLink to="/">Головна</NavLink><ChevronRight size={13} aria-hidden="true" /><strong>{current?.label ?? (pathname === '/search' ? 'Пошук' : 'Сторінку не знайдено')}</strong></span>
          <nav aria-label="Допоміжні переходи" className="utility-navigation">
            {utilityItems.map(({ path, label, icon: Icon }) => <NavLink key={path} to={path} className={({ isActive }) => `utility-nav-item ${isActive ? 'active' : ''}`}><Icon size={14} aria-hidden="true" /><span>{label}</span></NavLink>)}
          </nav>
        </div>
      </header>
      <div className="workspace">
        <main id="main" tabIndex={-1}><ErrorNotice error={logout.error} /><Outlet /></main>
      </div>
    </div>
  )
}
