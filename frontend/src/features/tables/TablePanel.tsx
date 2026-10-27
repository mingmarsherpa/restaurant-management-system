import { useState } from 'react'
import { Empty } from '../../components/Shared'
import { closeTableSession, tableQrUrl, type Table } from './api'
import { request } from '../orders/api'
import type { Order } from '../orders/api'

export function TablePanel({ tables, orders, onChange }: { tables: Table[]; orders: Order[]; onChange: (tables: Table[]) => void }) {
  const [editing, setEditing] = useState<number | 'new' | null>(null)
  const [error, setError] = useState('')

  const save = async (tableNumber: number, isActive: boolean, id?: number) => {
    setError('')
    try {
      const table = await request<Table>(id ? `/api/tables/${id}` : '/api/tables/', {
        method: id ? 'PATCH' : 'POST',
        body: JSON.stringify(id ? { table_number: tableNumber, is_active: isActive } : { table_number: tableNumber }),
      })
      onChange(id ? tables.map((value) => value.id === id ? table : value) : [...tables, table].sort((a, b) => a.table_number - b.table_number))
      setEditing(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save table')
    }
  }

  const remove = async (table: Table) => {
    if (!confirm(`Delete table ${table.table_number}?`)) return
    setError('')
    try {
      await request<void>(`/api/tables/${table.id}`, { method: 'DELETE' })
      onChange(tables.filter((value) => value.id !== table.id))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to delete table')
    }
  }

  const closeSession = async (table: Table) => {
    setError('')
    try {
      await closeTableSession(table.id)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to close table session')
    }
  }

  return <section className="content-grid">
    <div className="section-heading"><div><p className="eyebrow">Restaurant setup</p><h3>Tables</h3></div><button className="button primary" onClick={() => setEditing('new')}>+ Add table</button></div>
    {error && <div className="alert error">{error}</div>}
    {editing !== null && <TableForm table={editing === 'new' ? undefined : tables.find((table) => table.id === editing)} onCancel={() => setEditing(null)} onSave={save} />}
    <div className="card-list">
      {tables.length === 0 ? <Empty title="No tables yet" text="Add a table before accepting customer orders." /> : tables.map((table) => (
        <article className="resource-card" key={table.id}>
          <div className="resource-main"><span className="number">#{String(table.id).padStart(2, '0')}</span><div><h4>Table {table.table_number}</h4><p className="muted">{table.is_active ? 'Active and available for orders' : 'Inactive'} · {orders.filter((order) => order.table.id === table.id).length} active order(s)</p></div></div>
          <img className="table-qr" src={tableQrUrl(table.id)} alt={`QR code for table ${table.table_number}`} />
          <div className="actions"><button className="link-button" onClick={() => void closeSession(table)}>Close session</button><button className="link-button" onClick={() => setEditing(table.id)}>Edit</button><button className="link-button danger-text" onClick={() => void remove(table)}>Delete</button></div>
        </article>
      ))}
    </div>
  </section>
}

function TableForm({ table, onCancel, onSave }: { table?: Table; onCancel: () => void; onSave: (tableNumber: number, isActive: boolean, id?: number) => Promise<void> }) {
  const [tableNumber, setTableNumber] = useState(String(table?.table_number ?? ''))
  const [isActive, setIsActive] = useState(table?.is_active ?? true)
  return <form className="form-card compact" onSubmit={(event) => { event.preventDefault(); void onSave(Number(tableNumber), isActive, table?.id) }}>
    <div className="form-heading"><div><p className="eyebrow">{table ? 'Edit table' : 'New table'}</p><h3>{table ? `Table ${table.table_number}` : 'Add a table'}</h3></div><button type="button" className="close" onClick={onCancel}>×</button></div>
    <div className="form-fields"><label>Table number<input required min="1" type="number" value={tableNumber} onChange={(event) => setTableNumber(event.target.value)} /></label>{table && <label className="check"><input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />Active</label>}</div>
    <div className="form-actions"><button type="button" className="button ghost" onClick={onCancel}>Cancel</button><button className="button primary" type="submit">Save table</button></div>
  </form>
}
