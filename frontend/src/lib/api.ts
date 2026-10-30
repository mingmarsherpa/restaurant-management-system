import { API_URL } from '../config'

export const ACCESS_TOKEN_KEY = 'restaurant_access_token'

type ValidationError = {
  loc?: Array<string | number>
  msg?: string
}

type ErrorBody = {
  detail?: string | ValidationError[]
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

const formatValidationErrors = (errors: ValidationError[]) =>
  errors
    .map((error) => error.msg ?? 'Invalid request')
    .join('; ')

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    if (response.status === 401 && token) {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      window.dispatchEvent(new Event('auth-expired'))
    }
    const body = await response.json().catch(() => null) as ErrorBody | null
    const detail = Array.isArray(body?.detail)
      ? formatValidationErrors(body.detail)
      : body?.detail
    throw new ApiError(detail || `Request failed (${response.status})`, response.status)
  }

  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>
}
