import { useState } from 'react'
import { Empty } from '../../components/Shared'
import { money } from '../menu/api'
import { request } from './api'
import type { Bill } from './api'

export function BillsPanel({ bills, onChange }: { bills: Bill[]; onChange: (bills: Bill[]) => void }) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const selected = bills.find((bill) => bill.id === selectedId) ?? null

  const confirmPayment = async (bill: Bill) => {
    if (!window.confirm(`Confirm payment for Table ${bill.table_number}? This will close the dining session and complete all non-cancelled orders.`)) return
    setError('')
    try {
      const updated = await request<Bill>(`/api/admin/bills/${bill.id}/confirm-payment`, { method: 'POST' })
      onChange(bills.filter((value) => value.id !== updated.id))
      setSelectedId(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to confirm payment')
    }
  }

  if (bills.length === 0) return <Empty title="No open bills" text="Bills are created when a table has an open dining session." />

  return <section className="content-grid">
    <div className="section-heading"><div><p className="eyebrow">Payment desk</p><h3>Bills</h3></div></div>
    {error && <div className="alert error">{error}</div>}
    <div className="card-list">{bills.map((bill) => <article className="resource-card bill-card" key={bill.id}>
      <div>
        <p className="number">Bill #{bill.id}</p>
        <h4>Table {bill.table_number}</h4>
        <p className="muted">{bill.included_order_count} included order{bill.included_order_count === 1 ? '' : 's'} · {bill.excluded_cancelled_orders.length} cancelled excluded</p>
      </div>
      <strong className="bill-total">{money(bill.total_paisa)}</strong>
      <div className="actions">
        <button className="button ghost" onClick={() => setSelectedId(selectedId === bill.id ? null : bill.id)}>{selectedId === bill.id ? 'Hide details' : 'View bill'}</button>
        <button className="button primary" onClick={() => void confirmPayment(bill)}>Mark paid & confirm</button>
      </div>
      {selected?.id === bill.id && <div className="bill-details">
        {bill.included_orders.map((order) => <div className="order-item-row" key={order.id}><span>Order #{order.id} <span className="status">{order.status}</span></span><strong>{money(order.total_price_paisa)}</strong></div>)}
        {bill.excluded_cancelled_orders.length > 0 && <p className="muted">Cancelled orders are excluded from this total.</p>}
      </div>}
    </article>)}</div>
  </section>
}
