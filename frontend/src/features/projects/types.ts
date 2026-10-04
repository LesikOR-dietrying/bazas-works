import type { UserOption } from '../auth/types'

export const projectStatuses = ['PLANNED', 'IN_PROGRESS', 'TESTING', 'COMPLETED', 'FROZEN'] as const
export type ProjectStatus = typeof projectStatuses[number]
export interface Project {
  id: string; name: string; description: string; status: ProjectStatus; responsible_user_id: string;
  goal: string; start_date: string | null; deadline: string | null;
  responsible_name: string; participants: UserOption[]; created_at: string; updated_at: string;
}
export interface ProjectOption { id: string; name: string }
