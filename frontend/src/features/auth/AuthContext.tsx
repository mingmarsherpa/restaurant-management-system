import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { getCurrentUser, login as loginRequest } from './api'
import { ACCESS_TOKEN_KEY } from '../../lib/api'
import { AuthContext, type AuthContextValue } from './context'
import type { User } from './types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const restore = async () => {
      if (!localStorage.getItem(ACCESS_TOKEN_KEY)) {
        setLoading(false)
        return
      }
      try {
        setUser(await getCurrentUser())
      } catch {
        localStorage.removeItem(ACCESS_TOKEN_KEY)
      } finally {
        setLoading(false)
      }
    }
    void restore()

    const onExpired = () => {
      setUser(null)
      setLoading(false)
    }
    window.addEventListener('auth-expired', onExpired)
    return () => window.removeEventListener('auth-expired', onExpired)
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    login: async (identifier, password) => {
      const token = await loginRequest(identifier, password)
      localStorage.setItem(ACCESS_TOKEN_KEY, token.access_token)
      setUser(await getCurrentUser())
    },
    logout: () => {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      setUser(null)
    },
  }), [loading, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
