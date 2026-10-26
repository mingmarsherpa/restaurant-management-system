import { useState } from 'react'
import { Empty } from '../../components/Shared'
import { money } from '../menu/api'
import { request } from './api'
import type { Order } from './api'

const orderStatuses = ['pending', 'confirmed', 'preparing', 'ready', 'served', 'completed', 'cancelled']
const itemStatuses = ['pending', 'preparing', 'ready', 'completed', 'cancelled']

export function OrdersPanel({ orders, onChange }: { orders: Order[]; onChange: (orders: Order[]) => void }) {
  const [filter, setFilter] = useState('')
  const [error, setError] = useState('')
  const visible = filter ? orders.filter((order) => order.status === filter) : orders

  const update = async (path: string, value: string) => {
    setError('')
    try {
      const updated = await request<Order>(path, { method: 'PATCH', body: JSON.stringify({ status: value }) })
      onChange(orders.map((order) => order.id === updated.id ? updated : order))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to update order')
    }
  }

  return <section className="content-grid">
    <div className="section-heading">
      <div><p className="eyebrow">Live service</p><h3>Orders</h3></div>
      <select value={filter} onChange={(event) => setFilter(event.target.value)} aria-label="Filter orders">
        <option value="">All active orders</option>
        {orderStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
      </select>
    </div>
    {error && <div className="alert error">{error}</div>}
    {visible.length === 0 ? <Empty title="No active orders" text="New customer orders will appear here." /> : <div className="card-list">{visible.map((order) => (
      <article className="resource-card order-admin-card" key={order.id}>
        <div className="order-admin-main">
          <div className="resource-main"><span className="number">#{order.id}</span><div><h4>Table {order.table.table_number}</h4><p className="muted">{new Date(order.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} · {money(order.total_price_paisa)}</p></div></div>
          <select value={order.status} onChange={(event) => void update(`/api/admin/orders/${order.id}/status`, event.target.value)} aria-label={`Order ${order.id} status`}>
            {orderStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
        </div>
        <div className="order-items">
          {order.items.map((item) => <div className="order-item-row" key={item.id}>
            <span>{item.item_name} × {item.quantity}</span>
            <select value={item.status} onChange={(event) => void update(`/api/admin/orders/${order.id}/items/${item.id}/status`, event.target.value)} aria-label={`${item.item_name} status`}>
              {itemStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </div>)}
        </div>
      </article>
    ))}</div>}
  </section>
}
