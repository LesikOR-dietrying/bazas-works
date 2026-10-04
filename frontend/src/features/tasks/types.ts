export const taskStatuses = ['TODO', 'IN_PROGRESS', 'BLOCKED', 'TESTING', 'DONE'] as const
export const priorities = ['LOW', 'NORMAL', 'HIGH', 'CRITICAL'] as const
export type TaskStatus = typeof taskStatuses[number]
export type Priority = typeof priorities[number]
export interface Task {
  id: string; title: string; description: string; project_id: string; project_name: string;
  branch_id: string | null;
  assignee_id: string | null; assignee_name: string | null; created_by_id: string; created_by_name: string;
  status: TaskStatus; priority: Priority; deadline: string | null; result: string;
  completed_at: string | null; created_at: string; updated_at: string;
}
export interface TaskSummary { total: number; active: number; overdue: number; blocked: number; completed: number; completed_recently: number }
export function isOverdue(task: Task) { return task.status !== 'DONE' && task.deadline !== null && new Date(task.deadline).getTime() < Date.now() }
