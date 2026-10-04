import { Boxes, ClipboardCheck, FlaskConical, Gauge, ListChecks, Package, Settings, Wrench } from 'lucide-react'

export const navigation = [
  { path: '/', label: 'Dashboard', icon: Gauge },
  { path: '/rnd', label: 'R&D', icon: FlaskConical },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/production', label: 'Production', icon: Wrench },
  { path: '/inventory', label: 'Inventory', icon: Boxes },
  { path: '/tasks', label: 'My Tasks', icon: ListChecks },
  { path: '/my-work', label: 'My Work', icon: ClipboardCheck },
  { path: '/users', label: 'Admin Settings', icon: Settings, capability: 'ADMIN_USERS' },
] as const
