import { request as apiRequest } from '../../lib/api'

export const request = <T>(path: string, init?: RequestInit) =>
  apiRequest<T>(`/api/menu${path}`, init)

export const money = (paisa: number) => `Rs. ${(paisa / 100).toFixed(2)}`

export const pagePath = (path: string, page: number, pageSize: number) =>
  `${path}${path.includes('?') ? '&' : '?'}page=${page}&page_size=${pageSize}`
