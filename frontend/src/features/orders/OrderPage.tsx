import { useEffect, useMemo, useState } from 'react'
import { Empty } from '../../components/Shared'
import { money } from '../menu/api'
import type { Item } from '../menu/types'
import { claimOrderer, createTableOrder, getPublicTable, listTableOrders, request, type Order } from './api'

type CartLine = {
  key: string
  item: Item
  quantity: number
  optionIds: number[]
}

export function OrderPage({ onBack }: { onBack: () => void }) {
  const qrToken = new URLSearchParams(window.location.search).get('table') ?? ''
  const [tableNumber, setTableNumber] = useState<number | null>(null)
  const [tableId, setTableId] = useState<number | null>(null)
  const [ordererToken, setOrdererToken] = useState<string | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [cart, setCart] = useState<CartLine[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [orders, setOrders] = useState<Order[]>([])

  const loadOrders = async () => {
    try {
      setOrders(await listTableOrders(qrToken))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load current orders')
    }
  }

  useEffect(() => {
    const load = async () => {
      if (!qrToken) {
        setError('This ordering link does not include a table')
        setLoading(false)
        return
      }
      try {
        const [loadedTable, loadedItems, loadedOrders] = await Promise.all([
          getPublicTable(qrToken),
          request<{ items: Item[] }>('/api/menu/items?page=1&page_size=100'),
          listTableOrders(qrToken),
        ])
        setTableId(loadedTable.table_id)
        setTableNumber(loadedTable.table_number)
        const storedSessionId = sessionStorage.getItem(`orderer-session:${qrToken}`)
        if (storedSessionId === String(loadedTable.session_id)) {
          setOrdererToken(sessionStorage.getItem(`orderer-token:${qrToken}`))
        }
        setItems(loadedItems.items)
        setOrders(loadedOrders)
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : 'Unable to load ordering data')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [qrToken])

  useEffect(() => {
    if (!qrToken) return
    if (orders.length > 0 && orders.every((order) => ['completed', 'cancelled'].includes(order.status))) return
    const timer = window.setInterval(() => void loadOrders(), 7000)
    return () => window.clearInterval(timer)
  }, [qrToken, orders])

  const claimOrderingAccess = async () => {
    setError('')
    try {
      const claimed = await claimOrderer(qrToken)
      sessionStorage.setItem(`orderer-token:${qrToken}`, claimed.orderer_token)
      sessionStorage.setItem(`orderer-session:${qrToken}`, String(claimed.session_id))
      setOrdererToken(claimed.orderer_token)
      setNotice('You can now place orders for this table.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Another guest already has ordering access')
    }
  }

  const total = useMemo(
    () => cart.reduce((sum, line) => {
      const options = line.item.item_options
        .filter((option) => line.optionIds.includes(option.option_id))
        .reduce((value, option) => value + option.extra_price_paisa, 0)
      return sum + (line.item.base_price_paisa + options) * line.quantity
    }, 0),
    [cart],
  )

  const addItem = (item: Item) => {
    const key = `${item.id}:`
    setCart((current) => {
      const existing = current.find((line) => line.key === key)
      if (existing) {
        return current.map((line) => line.key === key ? { ...line, quantity: line.quantity + 1 } : line)
      }
      return [...current, { key, item, quantity: 1, optionIds: [] }]
    })
  }

  const updateQuantity = (key: string, delta: number) => {
    setCart((current) => current.flatMap((line) => {
      if (line.key !== key) return [line]
      const quantity = line.quantity + delta
      return quantity > 0 ? [{ ...line, quantity }] : []
    }))
  }

  const toggleOption = (key: string, optionId: number) => {
    setCart((current) => current.map((line) => {
      if (line.key !== key) return line
      const optionIds = line.optionIds.includes(optionId)
        ? line.optionIds.filter((id) => id !== optionId)
        : [...line.optionIds, optionId]
      return { ...line, optionIds }
    }))
  }

  const submit = async () => {
    if (tableId === null || cart.length === 0) return
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      const order = await createTableOrder(tableId, {
        items: cart.map((line) => ({
          item_id: line.item.id,
          quantity: line.quantity,
          option_ids: line.optionIds,
        })),
      }, ordererToken ?? '')
      setCart([])
      setNotice(`Order #${order.id} created for ${money(order.total_price_paisa)}`)
      setOrders((current) => [order, ...current])
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to create order')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="empty-state"><span className="loader" /> Loading ordering page...</div>

  return (
    <section className="content-grid">
      <div className="section-heading">
        <div><p className="eyebrow accent">Table {tableNumber ?? ''}</p><h3>{ordererToken ? 'Place an order' : 'Table menu'}</h3></div>
        <button className="button ghost" onClick={onBack}>Back to menu</button>
      </div>
      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}
      {!ordererToken && <div className="form-card"><p className="muted">You can view this table's menu and orders. One guest may claim ordering access.</p><button className="button primary" onClick={() => void claimOrderingAccess()}>Become ordering guest</button></div>}
      {orders.length > 0 && <section className="form-card">
        <div className="form-heading"><div><p className="eyebrow">Live updates</p><h3>Current orders</h3></div><span className="muted">Refreshes automatically</span></div>
        <div className="card-list">{orders.map((order) => <article className="customer-order" key={order.id}>
          <div className="form-heading"><strong>Order #{order.id}</strong><span className={`status status-${order.status}`}>{order.status}</span></div>
          {order.items.map((item) => <div className="order-item-row" key={item.id}><span>{item.item_name} × {item.quantity}</span><span className={`status status-${item.status}`}>{item.status}</span></div>)}
          <strong className="customer-total">{money(order.total_price_paisa)}</strong>
        </article>)}</div>
      </section>}
      <div className="order-layout">
        <div className="card-list">
          {items.length === 0 ? <Empty title="No dishes available" text="Add dishes in menu management first." /> : items.map((item) => (
            <article className="resource-card" key={item.id}>
              <div><h4>{item.name}</h4><p className="muted">{money(item.base_price_paisa)}</p></div>
              {ordererToken && <button className="button primary" onClick={() => addItem(item)}>Add</button>}
            </article>
          ))}
        </div>
        {ordererToken && <aside className="form-card order-cart">
          <div className="form-heading"><div><p className="eyebrow">Table order</p><h3>Cart</h3></div><strong>{money(total)}</strong></div>
          {cart.length === 0 ? <p className="muted">Add dishes to start this table's order.</p> : cart.map((line) => (
            <div className="cart-line" key={line.key}>
              <div>
                <strong>{line.item.name}</strong>
                <p className="muted">{money(line.item.base_price_paisa)} each</p>
                {line.item.item_options.length > 0 && <div className="cart-options">
                  {line.item.item_options.map((itemOption) => {
                    const option = line.item.option_groups.flatMap((group) => group.options).find((value) => value.id === itemOption.option_id)
                    return <label className="check" key={itemOption.option_id}><input type="checkbox" checked={line.optionIds.includes(itemOption.option_id)} onChange={() => toggleOption(line.key, itemOption.option_id)} />{option?.name ?? `Option ${itemOption.option_id}`}</label>
                  })}
                </div>}
              </div>
              <div className="actions"><button className="link-button" onClick={() => updateQuantity(line.key, -1)}>−</button><span>{line.quantity}</span><button className="link-button" onClick={() => updateQuantity(line.key, 1)}>+</button></div>
            </div>
          ))}
          <button className="button primary" disabled={submitting || tableId === null || cart.length === 0} onClick={() => void submit()}>{submitting ? 'Submitting...' : 'Submit order'}</button>
        </aside>}
      </div>
    </section>
  )
}
