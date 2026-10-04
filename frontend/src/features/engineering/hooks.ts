import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { Component, ComponentOption, Setup, SetupOption } from './types'
import { hasCapability } from '../auth/types'
import type { User } from '../auth/types'

export const useComponent = (id: string, enabled = true) => useQuery({ queryKey: ['component', id], enabled: Boolean(id) && enabled, queryFn: ({ signal }) => api<Component>(`/components/${id}`, { signal }) })
export const useComponentOptions = () => useQuery({ queryKey: ['component-options'], queryFn: ({ signal }) => api<ComponentOption[]>('/components/options', { signal }) })
export const useSetup = (id: string, enabled = true) => useQuery({ queryKey: ['setup', id], enabled: Boolean(id) && enabled, queryFn: ({ signal }) => api<Setup>(`/setups/${id}`, { signal }) })
export const useSetupOptions = (enabled = true) => useQuery({ queryKey: ['setup-options'], enabled, queryFn: ({ signal }) => api<SetupOption[]>('/setups/options', { signal }) })

export function canEditEngineering(user?: User | null) { return hasCapability(user, 'MANAGE_ENGINEERING') }
export function canManageProjectLinks(user?: User | null) { return hasCapability(user, 'MANAGE_PROJECTS') }
