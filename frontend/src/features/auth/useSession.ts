import { useQuery } from '@tanstack/react-query'
import { api, ApiError } from '../../api/client'
import { userSchema } from './types'

export function useSession() {
  return useQuery({ queryKey: ['auth'], retry: false, queryFn: async ({ signal }) => {
    try { return userSchema.parse(await api<unknown>('/auth/me', { signal })) }
    catch (error) { if (error instanceof ApiError && error.status === 401) return null; throw error }
  } })
}
