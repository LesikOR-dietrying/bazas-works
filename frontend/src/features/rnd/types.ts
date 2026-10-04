import type { SetupOption, FirmwareRevision } from '../engineering/types'

export const branchStatuses = ['OPEN', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'CLOSED'] as const
export type BranchStatus = typeof branchStatuses[number]
export type ConfigurationRole = 'BASELINE' | 'CANDIDATE'
export type PromotionStatus = 'REQUESTED' | 'APPROVED' | 'REJECTED'

export interface RndBranch {
  id: string; project_id: string; parent_id: string | null; parent_name: string | null
  name: string; purpose: string; status: BranchStatus; responsible_user_id: string
  responsible_name: string; change_summary: string; result_summary: string
  created_by_id: string; closed_at: string | null; created_at: string; updated_at: string
}

export interface BranchConfiguration {
  id: string; branch_id: string; setup_id: string; role: ConfigurationRole
  created_by_id: string; created_at: string; setup: SetupOption
}

export interface ValueChange { field: string; baseline: unknown; candidate: unknown }
export interface BomChange { component_id: string; component_name: string; position: string; baseline_quantity: number; candidate_quantity: number }
export interface ConfigurationComparison {
  baseline: SetupOption & { role: ConfigurationRole }
  candidate: SetupOption & { role: ConfigurationRole }
  attribute_changes: ValueChange[]; bom_changes: BomChange[]
}

export interface PromotionRequest {
  id: string; branch_id: string; candidate_setup_id: string; candidate_name: string
  status: PromotionStatus; reason: string; requested_by_id: string; requested_by_name: string
  reviewed_by_id: string | null; reviewed_by_name: string | null; reviewed_at: string | null
  review_notes: string; created_at: string
}

export type BranchFirmware = FirmwareRevision
