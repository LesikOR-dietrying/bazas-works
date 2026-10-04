import {
  Boxes,
  ClipboardCheck,
  Factory,
  FlaskConical,
  ListChecks,
  Package,
  Settings,
  ShoppingCart,
  Users,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Capability, User } from '../features/auth/types'
import { hasCapability } from '../features/auth/types'

export interface NavigationItem {
  path: string
  label: string
  icon: LucideIcon
  anyCapability?: readonly Capability[]
}

export const primaryNavigation: readonly NavigationItem[] = [
  { path: '/rnd', label: 'Розробка', icon: FlaskConical },
  { path: '/products', label: 'Продукція', icon: Package, anyCapability: ['VIEW_ENGINEERING'] },
  { path: '/orders', label: 'Замовлення', icon: ShoppingCart, anyCapability: ['MANAGE_ORDERS', 'MANAGE_PROCUREMENT'] },
  { path: '/production', label: 'Виробництво', icon: Factory, anyCapability: ['VIEW_PRODUCTION'] },
  { path: '/inventory', label: 'Склад', icon: Boxes, anyCapability: ['MANAGE_ORDERS', 'MANAGE_PROCUREMENT'] },
]

export const utilityNavigation: readonly NavigationItem[] = [
  { path: '/tasks', label: 'Мої задачі', icon: ListChecks },
  { path: '/my-work', label: 'Моя робота', icon: ClipboardCheck, anyCapability: ['VIEW_PRODUCTION'] },
  { path: '/users', label: 'Користувачі', icon: Users, anyCapability: ['ADMIN_USERS'] },
  { path: '/settings', label: 'Налаштування', icon: Settings, anyCapability: ['ADMIN_USERS'] },
]

export const navigation = [...primaryNavigation, ...utilityNavigation] as const

export function canOpenNavigationItem(user: User | null | undefined, item: NavigationItem) {
  return !item.anyCapability || item.anyCapability.some(capability => hasCapability(user, capability))
}

export function visibleNavigation(items: readonly NavigationItem[], user: User | null | undefined) {
  return items.filter(item => canOpenNavigationItem(user, item))
}
