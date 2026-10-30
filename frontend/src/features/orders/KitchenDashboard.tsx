import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../auth/useAuth'
import { OrdersPanel } from './OrdersPanel'
import { request, type Order } from './api'

export function KitchenDashboard() {
  const { user, logout } = useAuth()
  const [orders, setOrders] = useState<Order[]>([])
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    try {
      setOrders(await request<Order[]>('/api/admin/orders'))
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load orders')
    }
  }, [])

  useEffect(() => {
    const initialLoad = async () => {
      await load()
    }
    void initialLoad()
  }, [load])

  return <main className="shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark">R</span><div><p className="eyebrow">Kitchen workspace</p><h1>Order service</h1></div></div>
      <div className="staff-actions"><span className="muted">{user?.username}</span><button className="button ghost" onClick={logout}>Logout</button></div>
    </header>
    <section className="intro"><div><p className="eyebrow accent">Kitchen</p><h2>Keep orders moving.</h2><p className="muted">View active orders and update their progress.</p></div></section>
    {error && <div className="alert error">{error}</div>}
    <OrdersPanel orders={orders} onChange={setOrders} />
  </main>
}
