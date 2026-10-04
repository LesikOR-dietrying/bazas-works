import { z } from 'zod'

export const roleCodes = ['ADMINISTRATOR', 'ENGINEER', 'RND_ENGINEER', 'PRODUCTION_MANAGER', 'PROCUREMENT_SPECIALIST', 'ASSEMBLER', 'ELECTRONICS_TECHNICIAN', 'FIRMWARE_ENGINEER', 'TEST_PILOT', 'TEST_ENGINEER', 'QUALITY_CONTROLLER'] as const
export type RoleCode = typeof roleCodes[number]
export type Capability = 'ADMIN_USERS' | 'VIEW_ALL_PROJECTS' | 'MANAGE_PROJECTS' | 'MANAGE_TASKS' | 'VIEW_ENGINEERING' | 'MANAGE_ENGINEERING' | 'MANAGE_ALL_FILES' | 'VIEW_RND_DASHBOARD' | 'VIEW_PRODUCTION' | 'MANAGE_ORDERS' | 'APPROVE_DEVIATIONS' | 'MANAGE_PROCUREMENT'

export const roleLabels: Record<RoleCode, string> = {
  ADMINISTRATOR: 'Адміністратор', ENGINEER: 'Інженер', RND_ENGINEER: 'R&D інженер',
  PRODUCTION_MANAGER: 'Керівник виробництва', PROCUREMENT_SPECIALIST: 'Спеціаліст із закупівель',
  ASSEMBLER: 'Складальник', ELECTRONICS_TECHNICIAN: 'Технік-електронік',
  FIRMWARE_ENGINEER: 'Інженер прошивок', TEST_PILOT: 'Тест-пілот', TEST_ENGINEER: 'Інженер-випробувач',
  QUALITY_CONTROLLER: 'Контролер якості',
}

export const userSchema = z.object({
  id: z.string().uuid(), username: z.string(), full_name: z.string(), email: z.string().email().nullable(),
  role: z.enum(['ADMIN', 'MANAGER', 'ENGINEER', 'EMPLOYEE']), roles: z.array(z.enum(roleCodes)),
  capabilities: z.array(z.string()), is_active: z.boolean(), created_at: z.string(), updated_at: z.string(),
})
export type User = z.infer<typeof userSchema>
export interface UserOption { id: string; full_name: string }
export function hasCapability(user: User | null | undefined, capability: Capability) { return user?.capabilities.includes(capability) ?? false }
