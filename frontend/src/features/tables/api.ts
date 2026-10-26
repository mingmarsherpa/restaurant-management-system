import { request } from '../orders/api'

export type Table = {
  id: number
  table_number: number
  qr_code_token: string
  is_active: boolean
}

export const listTables = () => request<Table[]>('/api/tables/')
