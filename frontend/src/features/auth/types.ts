export type Role = 'admin' | 'kitchen'

export type User = {
  id: number
  username: string
  email: string
  role: Role
  is_active: boolean
  created_at: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  role: Role
}
