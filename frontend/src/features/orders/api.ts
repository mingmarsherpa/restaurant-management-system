import type { Item, Pagination } from '../menu/types'

import { API_URL } from '../../config'

type ValidationError = {
  loc?: Array<string | number>
  msg?: string
}

type ErrorBody = {
  detail?: string | ValidationError[]
}

export class ApiError extends Error {
  readonly status: number

  constructor(
    message: string,
    status: number,
  ) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

const formatValidationErrors = (errors: ValidationError[]) =>
  errors
    .map((error) => {
      const location = error.loc
        ?.filter((part) => part !== 'body')
        .reduce(
          (value, part) => typeof part === 'number' ? `${value}[${part}]` : value ? `${value}.${part}` : part,
          '',
        )
      return location && error.msg ? `${location}: ${error.msg}` : error.msg ?? 'Invalid request'
    })
    .join('; ')

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null) as ErrorBody | null
    const detail = Array.isArray(body?.detail)
      ? formatValidationErrors(body.detail)
      : body?.detail
    throw new ApiError(detail || `Request failed (${response.status})`, response.status)
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

export type OrderCreate = {
  items: Array<{
    item_id: number
    quantity: number
    option_ids: number[]
  }>
}

type OrderCreateInput = OrderCreate | { items: Array<OrderCreate['items'][number] | number> }

const normalizeOrderPayload = (payload: OrderCreateInput): OrderCreate => ({
  items: payload.items.map((item) => typeof item === 'number'
    ? { item_id: item, quantity: 1, option_ids: [] }
    : item),
})

export const getPublicTable = (qrToken: string) =>
  request<PublicTable>(`/api/public/tables/${qrToken}`)

export const claimOrderer = (qrToken: string) =>
  request<OrdererClaim>(`/api/public/tables/${qrToken}/claim-orderer`, { method: 'POST' })

export const listTableOrders = (qrToken: string) =>
  request<Order[]>(`/api/public/tables/${qrToken}/orders`)

export const createTableOrder = (tableId: number, payload: OrderCreateInput, ordererToken: string) =>
  request<Order>(`/api/tables/${tableId}/orders`, {
    method: 'POST',
    headers: { 'X-Orderer-Token': ordererToken },
    body: JSON.stringify(normalizeOrderPayload(payload)),
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

export type Bill = {
  id: number
  dining_session_id: number
  table_id: number
  table_number: number
  status: string
  subtotal_paisa: number
  total_paisa: number
  included_order_count: number
  created_at: string
  paid_at: string | null
  confirmed_at: string | null
  included_orders: Order[]
  excluded_cancelled_orders: Order[]
}
