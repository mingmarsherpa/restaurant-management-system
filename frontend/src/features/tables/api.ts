import { request } from '../orders/api'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Table = {
  id: number
  table_number: number
  qr_code_token: string
  is_active: boolean
}

export const listTables = () => request<Table[]>('/api/tables/')

export const tableQrUrl = (tableId: number) => `${API_URL}/api/tables/${tableId}/qr`

export const closeTableSession = (tableId: number) =>
  request<void>(`/api/admin/tables/${tableId}/sessions/close`, { method: 'POST' })
