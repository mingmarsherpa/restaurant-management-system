import { createContext } from 'react'
import type { User } from './types'

export type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (identifier: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
