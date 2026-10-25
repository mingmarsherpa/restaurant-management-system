import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Empty, PaginationControls } from '../../components/Shared'
import { money, request } from './api'
import type { Item, Mutate, Option, OptionGroup, Pagination } from './types'

export function ItemsPanel({ items, groups, options, pagination, onPageChange, mutate }: { items: Item[]; groups: OptionGroup[]; options: Option[]; pagination: Pagination; onPageChange: (page: number) => void; mutate: Mutate }) {
  const [editing, setEditing] = useState<number | 'new' | null>(null)
  return (
    <section className="content-grid">
      <div className="section-heading"><div><p className="eyebrow">Your menu</p><h3>Dishes</h3></div><button className="button primary" onClick={() => setEditing('new')}>+ Add dish</button></div>
      {editing !== null && <ItemForm item={editing === 'new' ? undefined : items.find((item) => item.id === editing)} groups={groups} options={options} onCancel={() => setEditing(null)} mutate={mutate} />}
      <div className="card-list">
        {items.length === 0 ? <Empty title="No dishes yet" text="Add your first dish to start building the menu." /> : items.map((item) => (
          <article className="resource-card" key={item.id}>
            <div className="resource-main"><span className="number">#{String(item.id).padStart(2, '0')}</span><div><h4>{item.name}</h4><p className="muted">{item.option_groups.length ? item.option_groups.map((group) => group.name).join(' · ') : 'No option groups assigned'}</p></div></div>
            <strong className="price">{money(item.base_price_paisa)}</strong>
            <div className="actions"><button className="link-button" onClick={() => setEditing(item.id)}>Edit</button><button className="link-button danger-text" onClick={() => { if (confirm(`Delete ${item.name}?`)) void mutate(() => request<void>(`/items/${item.id}`, { method: 'DELETE' }), 'Dish deleted') }}>Delete</button></div>
          </article>
        ))}
      </div>
      <PaginationControls page={pagination.page} totalPages={pagination.total_pages} onPageChange={onPageChange} />
    </section>
  )
}

function ItemForm({ item, groups, options, onCancel, mutate }: { item?: Item; groups: OptionGroup[]; options: Option[]; onCancel: () => void; mutate: Mutate }) {
  const [name, setName] = useState(item?.name ?? '')
  const [price, setPrice] = useState(item ? String(item.base_price_paisa / 100) : '')
  const [selectedGroups, setSelectedGroups] = useState<number[]>(item?.option_groups.map((group) => group.id) ?? [])
  const [selectedOptions, setSelectedOptions] = useState<Record<number, string>>(
    Object.fromEntries(item?.item_options.map((entry) => [entry.option_id, String(entry.extra_price_paisa / 100)]) ?? []),
  )
  const availableOptions = useMemo(() => options.filter((option) => selectedGroups.includes(option.group_id)), [options, selectedGroups])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const payload = {
      name: name.trim(),
      base_price_paisa: Math.round(Number(price || 0) * 100),
      option_group_ids: selectedGroups,
      item_options: Object.entries(selectedOptions).filter(([id]) => availableOptions.some((option) => option.id === Number(id))).map(([id, value]) => ({ option_id: Number(id), extra_price_paisa: Math.round(Number(value || 0) * 100) })),
    }
    void mutate(async () => {
      await request<Item>(item ? `/items/${item.id}` : '/items', { method: item ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
      onCancel()
    }, item ? 'Dish updated' : 'Dish added')
  }
  return <form className="form-card" onSubmit={submit}><div className="form-heading"><div><p className="eyebrow">{item ? 'Edit dish' : 'New dish'}</p><h3>{item ? item.name : 'Add a dish'}</h3></div><button type="button" className="close" onClick={onCancel}>×</button></div><div className="form-fields"><label>Dish name<input required maxLength={150} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Classic burger" /></label><label>Base price (Rs.)<input required min="0" step="0.01" type="number" value={price} onChange={(event) => setPrice(event.target.value)} placeholder="0.00" /></label></div><fieldset><legend>Option groups</legend><div className="check-grid">{groups.map((group) => <label className="check" key={group.id}><input type="checkbox" checked={selectedGroups.includes(group.id)} onChange={() => setSelectedGroups((current) => current.includes(group.id) ? current.filter((id) => id !== group.id) : [...current, group.id])} />{group.name}</label>)}</div></fieldset>{availableOptions.length > 0 && <fieldset><legend>Extra prices <small>(optional)</small></legend><div className="option-prices">{availableOptions.map((option) => <label key={option.id}>{option.name}<input type="number" min="0" step="0.01" placeholder="0.00" value={selectedOptions[option.id] ?? ''} onChange={(event) => setSelectedOptions((current) => ({ ...current, [option.id]: event.target.value }))} /></label>)}</div></fieldset>}<div className="form-actions"><button type="button" className="button ghost" onClick={onCancel}>Cancel</button><button className="button primary" type="submit">Save dish</button></div></form>
}
