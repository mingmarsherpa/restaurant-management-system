import { request } from '../../lib/api'
import type { LoginResponse, User } from './types'

export const login = (identifier: string, password: string) =>
  request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ identifier, password }),
  })

export const getCurrentUser = () => request<User>('/api/auth/me')
