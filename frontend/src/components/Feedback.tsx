import type { ReactNode } from 'react'

export function ErrorNotice({ error }: { error: unknown }) {
  if (!error) return null
  return <p role="alert" className="error-notice">{error instanceof Error ? error.message : 'Не вдалося виконати дію.'}</p>
}

export function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return <label className="form-field"><span>{label}</span>{children}{error && <small role="alert" className="field-error">{error}</small>}</label>
}

export function Loading() { return <p role="status" className="loading-state">Завантаження…</p> }
