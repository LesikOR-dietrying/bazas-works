export const componentCategories = ['MOTOR', 'ESC', 'FLIGHT_CONTROLLER', 'PROPELLER', 'BATTERY', 'CAMERA', 'VTX', 'RX', 'GPS', 'ANTENNA', 'FRAME', 'POWER_MODULE', 'OTHER'] as const
export const setupStatuses = ['DEVELOPMENT', 'TESTING', 'READY', 'DEPRECATED'] as const

export type ComponentCategory = typeof componentCategories[number]
export type SetupStatus = typeof setupStatuses[number]

export interface Component {
  id: string; category: ComponentCategory; manufacturer: string; model: string; name: string
  description: string; specifications: Record<string, unknown>; datasheet_url: string | null
  notes: string; created_at: string; updated_at: string
}

export interface ComponentOption { id: string; name: string; category: ComponentCategory; manufacturer: string; model: string }

export interface Setup {
  id: string; name: string; drone_class: string; version: string; status: SetupStatus
  description: string; weight_kg: string | null; payload_kg: string | null
  battery_description: string; battery_voltage: string | null; battery_capacity_ah: string | null
  propeller_description: string; flight_time_minutes: string | null; average_current_a: string | null
  max_current_a: string | null; firmware_type: string; firmware_version: string; notes: string
  attributes: Record<string, unknown>
  created_at: string; updated_at: string
}

export interface SetupOption { id: string; name: string; version: string; status: SetupStatus }

export interface SetupComponent {
  id: string; setup_id: string; component_id: string; quantity: number; position: string; notes: string
  component: ComponentOption; created_at: string; updated_at: string
}

export interface FirmwareRevision {
  id: string; setup_id: string; version_name: string; firmware_type: string; firmware_version: string
  description: string; config_text: string; created_at: string; created_by_id: string
  created_by_name?: string
}
