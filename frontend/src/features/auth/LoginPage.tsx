import { useState } from 'react'
import type { FormEvent } from 'react'
import { useAuth } from './useAuth'

export function LoginPage() {
  const { login } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(identifier, password)
      window.history.replaceState({}, '', '/admin')
      window.dispatchEvent(new PopStateEvent('popstate'))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to log in')
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="auth-page">
    <form className="form-card auth-card" onSubmit={(event) => void submit(event)}>
      <div>
        <p className="eyebrow accent">Restaurant staff</p>
        <h2>Sign in</h2>
        <p className="muted">Use your staff account to access the workspace.</p>
      </div>
      {error && <div className="alert error">{error}</div>}
      <label>Username or email<input value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" required /></label>
      <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required /></label>
      <button className="button primary" disabled={submitting}>{submitting ? 'Signing in...' : 'Sign in'}</button>
    </form>
  </main>
}
