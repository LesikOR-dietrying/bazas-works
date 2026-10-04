export class ApiError extends Error {
  constructor(public readonly status: number, message = `Помилка запиту (${status})`) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function getJson(path: string, signal?: AbortSignal): Promise<unknown> {
  return api<unknown>(path, { signal })
}

async function request(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (options.method && options.method !== 'GET') {
    const csrf = document.cookie.split('; ').find(value => value.startsWith('baza_csrf='))?.split('=')[1]
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf))
  }
  let response: Response
  try { response = await fetch(`/api${path}`, { ...options, headers, credentials: 'same-origin' }) }
  catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new Error('Сервер недоступний. Перевірте з’єднання та спробуйте ще раз.')
  }
  if (!response.ok) {
    let message = response.status === 422 ? 'Перевірте заповнення полів.' : `Помилка запиту (${response.status})`
    const body: unknown = await response.json().catch(() => null)
    if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') message = body.detail
    if (response.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('baza:unauthorized'))
    throw new ApiError(response.status, message)
  }
  return response
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await request(path, options)
  return (response.status === 204 ? undefined : await response.json()) as T
}

export async function apiBlob(path: string): Promise<Blob> {
  const response = await request(path)
  return response.blob()
}

export const send = <T>(path: string, method: string, data?: unknown) =>
  api<T>(path, { method, ...(data === undefined ? {} : { body: JSON.stringify(data) }) })

export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
