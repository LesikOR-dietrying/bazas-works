import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { UserOption } from '../auth/types'
import type { Project, ProjectOption } from './types'

export const useUserOptions = () => useQuery({ queryKey: ['user-options'], queryFn: ({ signal }) => api<UserOption[]>('/users/options', { signal }) })
export const useProjectOptions = () => useQuery({ queryKey: ['project-options'], queryFn: ({ signal }) => api<ProjectOption[]>('/projects/options', { signal }) })
export const useProject = (id: string) => useQuery({ queryKey: ['project', id], enabled: Boolean(id), queryFn: ({ signal }) => api<Project>(`/projects/${id}`, { signal }) })
