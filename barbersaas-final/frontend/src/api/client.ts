const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

let refreshInProgress: Promise<void> | null = null

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json')
  const token = localStorage.getItem('barbersaas_token')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 204) return undefined as T
  const body = await response.json().catch(() => null)
  if (response.status === 401 && !path.startsWith('/auth/')) {
    localStorage.removeItem('barbersaas_token')
    if (!refreshInProgress) {
      refreshInProgress = Promise.resolve().then(() => window.location.reload()).finally(() => { refreshInProgress = null })
    }
    await refreshInProgress
  }
  if (!response.ok) throw new Error(body?.detail ?? `HTTP ${response.status}`)
  return body as T
}
