export const testTypes = ['MOTOR_BENCH', 'ESC_BENCH', 'BATTERY', 'PROPELLER', 'FLIGHT', 'ENDURANCE', 'RANGE', 'TEMPERATURE', 'FRAME', 'ANTENNA', 'OTHER'] as const
export const testStatuses = ['PLANNED', 'IN_PROGRESS', 'PASS', 'FAIL', 'PARTIAL'] as const
export const equipmentRoles = ['ESC', 'PROPELLER', 'BATTERY', 'OTHER'] as const
export type TestType = typeof testTypes[number]
export type TestStatus = typeof testStatuses[number]
export type EquipmentRole = typeof equipmentRoles[number]

export interface TestRecord {
  id: string; name: string; test_type: TestType; project_id: string | null; setup_id: string | null
  branch_id: string | null
  component_id: string | null; firmware_revision_id: string | null; performed_by_id: string | null
  test_date: string | null; status: TestStatus; description: string
  conditions: Record<string, unknown>; result_summary: Record<string, unknown>; conclusion: string
  created_at: string; updated_at: string
  project_name?: string | null; setup_name?: string | null; component_name?: string | null; performed_by_name?: string | null
}

export const measurementFields = [
  ['throttle_percent', 'Газ (%)'], ['voltage_v', 'Напруга (В)'], ['current_a', 'Струм (А)'],
  ['power_w', 'Потужність (Вт)'], ['rpm', 'Оберти (RPM)'], ['thrust_kg', 'Тяга (кг)'],
  ['efficiency_g_w', 'Ефективність (г/Вт)'], ['motor_temperature_c', 'Температура двигуна (°C)'],
  ['esc_temperature_c', 'Температура ESC (°C)'], ['timestamp_seconds', 'Час (с)'],
] as const
export type MeasurementField = typeof measurementFields[number][0]
export interface TestMeasurement {
  id: string; test_id: string; sequence: number; created_at: string; updated_at: string
  throttle_percent: string | null; voltage_v: string | null; current_a: string | null; power_w: string | null
  rpm: string | null; thrust_kg: string | null; efficiency_g_w: string | null
  motor_temperature_c: string | null; esc_temperature_c: string | null; timestamp_seconds: string | null
}

export interface TestEquipment {
  id: string; test_id: string; component_id: string; role: EquipmentRole; notes: string; created_at: string
  component: { id: string; name: string; category: string }
}
