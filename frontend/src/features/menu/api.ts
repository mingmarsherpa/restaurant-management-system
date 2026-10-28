import { API_URL } from '../../config'

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}/api/menu${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const money = (paisa: number) => `Rs. ${(paisa / 100).toFixed(2)}`

export const pagePath = (path: string, page: number, pageSize: number) =>
  `${path}${path.includes('?') ? '&' : '?'}page=${page}&page_size=${pageSize}`
