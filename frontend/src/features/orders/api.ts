import type { Item, Pagination } from '../menu/types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>
}

export type Table = {
  id: number
  table_number: number
  is_active: boolean
}

export type PublicTable = {
  table_id: number
  table_number: number
  session_id: number
  session_status: string
}

export type OrdererClaim = {
  orderer_token: string
  session_id: number
}

export const getPublicTable = (qrToken: string) =>
  request<PublicTable>(`/api/public/tables/${qrToken}`)

export const claimOrderer = (qrToken: string) =>
  request<OrdererClaim>(`/api/public/tables/${qrToken}/claim-orderer`, { method: 'POST' })

export const listTableOrders = (qrToken: string) =>
  request<Order[]>(`/api/public/tables/${qrToken}/orders`)

export const createTableOrder = (tableId: number, payload: unknown, ordererToken: string) =>
  request<Order>(`/api/tables/${tableId}/orders`, {
    method: 'POST',
    headers: { 'X-Orderer-Token': ordererToken },
    body: JSON.stringify(payload),
  })

export type MenuPage = {
  items: Item[]
  pagination: Pagination
}

export type OrderItem = {
  id: number
  item_id: number
  item_name: string
  quantity: number
  unit_price_paisa: number
  status: string
  selected_options: { option_id: number; option_name: string; extra_price_paisa: number }[]
}

export type Order = {
  id: number
  session_id: number
  status: string
  total_price_paisa: number
  created_at: string
  table: { id: number; table_number: number }
  items: OrderItem[]
}
