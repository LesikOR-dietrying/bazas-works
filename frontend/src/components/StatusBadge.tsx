import { labelForCode } from '../lib/labels'

export function StatusBadge({ value }: { value: string }) {
  return <span className={`status-badge status-${value.toLowerCase()}`}>{labelForCode(value)}</span>
}
