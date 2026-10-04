import { ChevronRight, Hexagon, LogOut, Search } from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { navigation } from '../app/navigation'
import { useSession } from '../features/auth/useSession'
import { replaceSession } from '../features/auth/sessionCache'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { send } from '../api/client'
import { Button } from './ui/button'
import { ErrorNotice } from './Feedback'
import { Input } from './ui/input'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { hasCapability, roleLabels } from '../features/auth/types'

export function Layout() {
  const { pathname } = useLocation()
  const current = navigation.find((item) => item.path === '/' ? pathname === '/' : pathname.startsWith(item.path))
  const { data: user } = useSession()
  const cache = useQueryClient()
  const navigate = useNavigate(), [search, setSearch] = useState('')
  const logout = useMutation({ mutationFn: () => send('/auth/logout', 'POST'), onSuccess: () => replaceSession(cache, null) })
  const visibleNavigation = navigation.filter(item => !('capability' in item) || hasCapability(user, item.capability))
  const primaryNavigation = visibleNavigation.slice(0, 5)
  const personalNavigation = visibleNavigation.slice(5, 7)
  const administrationNavigation = visibleNavigation.slice(7)
  const CurrentIcon = current?.icon
  function submitSearch(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (search.trim()) { navigate(`/search?q=${encodeURIComponent(search.trim())}`); setSearch('') } }

  const renderNavigation = (items: typeof visibleNavigation) => items.map(({ path, label, icon: Icon }) => (
    <NavLink key={path} to={path} aria-label={label} end={path === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
      <Icon size={18} strokeWidth={1.8} aria-hidden="true" /><span>{label}</span><ChevronRight className="nav-chevron" size={14} aria-hidden="true" />
    </NavLink>
  ))

  return (
    <div className="app-shell">
      <a href="#main" className="skip-link">Перейти до вмісту</a>
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="BAZA — головна">
          <span className="brand-symbol"><Hexagon size={28} strokeWidth={1.7} /></span>
          <span>BAZA<span className="brand-caption">ENGINEERING WORKSPACE</span></span>
        </NavLink>
        <nav aria-label="Головна навігація" className="sidebar-navigation">
          <p className="nav-heading">ОСНОВНІ МОДУЛІ</p>
          {renderNavigation(primaryNavigation)}
          <p className="nav-heading">МОЯ РОБОТА</p>
          {renderNavigation(personalNavigation)}
          {!!administrationNavigation.length && <><p className="nav-heading">КЕРУВАННЯ</p>{renderNavigation(administrationNavigation)}</>}
        </nav>
        <div className="sidebar-footer"><span className="environment-dot" /><div><strong>Внутрішня система</strong><small>BAZA · Engineering OS</small></div></div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="breadcrumb">{CurrentIcon && <CurrentIcon size={17} aria-hidden="true" />}<span>BAZA</span><ChevronRight size={13} aria-hidden="true" /><strong>{current?.label ?? (pathname === '/search' ? 'Пошук' : pathname.startsWith('/users') ? 'Користувачі' : pathname === '/settings' ? 'Налаштування' : 'Сторінку не знайдено')}</strong></span>
          <form role="search" className="top-search" onSubmit={submitSearch}><Search size={16} aria-hidden="true" /><Input aria-label="Глобальний пошук" value={search} onChange={event => setSearch(event.target.value)} placeholder="Пошук проєктів, виробів, задач…" /><button className="search-submit" type="submit" aria-label="Знайти"><ChevronRight size={15} /></button></form>
          <div className="account-menu"><span className="user-avatar" aria-hidden="true">{user?.full_name?.charAt(0).toUpperCase()}</span><span className="user-copy"><strong>{user?.full_name}</strong><small>{user?.roles?.[0] ? roleLabels[user.roles[0]] : user?.role}</small></span><Button className="logout-button" variant="outline" aria-label="Вийти" title="Вийти" disabled={logout.isPending} onClick={() => logout.mutate()}><LogOut size={16} /></Button></div>
        </header>
        <main id="main" tabIndex={-1}><ErrorNotice error={logout.error} /><Outlet /></main>
      </div>
    </div>
  )
}
