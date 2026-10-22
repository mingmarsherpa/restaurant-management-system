import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Tab = 'items' | 'groups' | 'options'

type Option = { id: number; name: string; group_id: number }
type OptionGroup = { id: number; name: string; options: Option[] }
type ItemOptionPrice = { option_id: number; extra_price_paisa: number }
type Item = {
  id: number
  name: string
  base_price_paisa: number
  option_groups: OptionGroup[]
  item_options: ItemOptionPrice[]
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}/api/menu${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

const money = (paisa: number) => `Rs. ${(paisa / 100).toFixed(2)}`

function App() {
  const [tab, setTab] = useState<Tab>('items')
  const [items, setItems] = useState<Item[]>([])
  const [groups, setGroups] = useState<OptionGroup[]>([])
  const [options, setOptions] = useState<Option[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [loadedItems, loadedGroups, loadedOptions] = await Promise.all([
        request<Item[]>('/items'),
        request<OptionGroup[]>('/option-groups'),
        request<Option[]>('/options'),
      ])
      setItems(loadedItems)
      setGroups(loadedGroups)
      setOptions(loadedOptions)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load menu data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const initialLoad = async () => {
      await load()
    }
    void initialLoad()
  }, [])

  const mutate = async (action: () => Promise<void>, message: string) => {
    setError('')
    setNotice('')
    try {
      await action()
      await load()
      setNotice(message)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The request failed')
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">R</span>
          <div>
            <p className="eyebrow">Restaurant admin</p>
            <h1>Menu studio</h1>
          </div>
        </div>
        <button className="button ghost" onClick={() => void load()} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh data'}
        </button>
      </header>

      <section className="intro">
        <div>
          <p className="eyebrow accent">Menu management</p>
          <h2>Keep your menu simple and up to date.</h2>
          <p className="muted">Manage dishes, option groups, and choices from one place.</p>
        </div>
        <div className="stats">
          <Stat label="Dishes" value={items.length} />
          <Stat label="Groups" value={groups.length} />
          <Stat label="Choices" value={options.length} />
        </div>
      </section>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <nav className="tabs" aria-label="Menu resources">
        {(['items', 'groups', 'options'] as Tab[]).map((value) => (
          <button
            key={value}
            className={tab === value ? 'tab active' : 'tab'}
            onClick={() => setTab(value)}
          >
            {value === 'items' ? 'Dishes' : value === 'groups' ? 'Option groups' : 'Choices'}
            <span>{value === 'items' ? items.length : value === 'groups' ? groups.length : options.length}</span>
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="empty-state"><span className="loader" /> Loading your menu...</div>
      ) : tab === 'items' ? (
        <ItemsPanel items={items} groups={groups} options={options} mutate={mutate} />
      ) : tab === 'groups' ? (
        <GroupsPanel groups={groups} mutate={mutate} />
      ) : (
        <OptionsPanel groups={groups} options={options} mutate={mutate} />
      )}
    </main>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="stat"><strong>{value.toString().padStart(2, '0')}</strong><span>{label}</span></div>
}

type Mutate = (action: () => Promise<void>, message: string) => Promise<void>

function ItemsPanel({ items, groups, options, mutate }: { items: Item[]; groups: OptionGroup[]; options: Option[]; mutate: Mutate }) {
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

function GroupsPanel({ groups, mutate }: { groups: OptionGroup[]; mutate: Mutate }) {
  const [editing, setEditing] = useState<number | 'new' | null>(null)
  return <section className="content-grid"><div className="section-heading"><div><p className="eyebrow">Organize choices</p><h3>Option groups</h3></div><button className="button primary" onClick={() => setEditing('new')}>+ Add group</button></div>{editing !== null && <GroupForm group={editing === 'new' ? undefined : groups.find((group) => group.id === editing)} onCancel={() => setEditing(null)} mutate={mutate} />}{groups.length === 0 ? <Empty title="No option groups yet" text="Create a group like Size, Milk, or Toppings." /> : <div className="group-grid">{groups.map((group) => <article className="resource-card group-card" key={group.id}><div><span className="number">#{String(group.id).padStart(2, '0')}</span><h4>{group.name}</h4><p className="muted">{group.options.length} choice{group.options.length === 1 ? '' : 's'}</p></div><div className="group-options">{group.options.map((option) => <span key={option.id}>{option.name}</span>)}</div><div className="actions"><button className="link-button" onClick={() => setEditing(group.id)}>Edit</button><button className="link-button danger-text" onClick={() => { if (confirm(`Delete ${group.name}?`)) void mutate(() => request<void>(`/option-groups/${group.id}`, { method: 'DELETE' }), 'Option group deleted') }}>Delete</button></div></article>)}</div>}</section>
}

function GroupForm({ group, onCancel, mutate }: { group?: OptionGroup; onCancel: () => void; mutate: Mutate }) {
  const [name, setName] = useState(group?.name ?? '')
  const submit = (event: FormEvent) => { event.preventDefault(); void mutate(async () => { await request<OptionGroup>(group ? `/option-groups/${group.id}` : '/option-groups', { method: group ? 'PATCH' : 'POST', body: JSON.stringify(group ? { name: name.trim() } : { name: name.trim(), options: [] }) }); onCancel() }, group ? 'Option group updated' : 'Option group added') }
  return <form className="form-card compact" onSubmit={submit}><div className="form-heading"><div><p className="eyebrow">{group ? 'Edit group' : 'New group'}</p><h3>{group ? group.name : 'Add an option group'}</h3></div><button type="button" className="close" onClick={onCancel}>×</button></div><label>Group name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Toppings" /></label><div className="form-actions"><button type="button" className="button ghost" onClick={onCancel}>Cancel</button><button className="button primary" type="submit">Save group</button></div></form>
}

function OptionsPanel({ groups, options, mutate }: { groups: OptionGroup[]; options: Option[]; mutate: Mutate }) {
  const [editing, setEditing] = useState<number | 'new' | null>(null)
  return <section className="content-grid"><div className="section-heading"><div><p className="eyebrow">Choices in your groups</p><h3>Options</h3></div><button className="button primary" onClick={() => setEditing('new')}>+ Add choice</button></div>{editing !== null && <OptionForm option={editing === 'new' ? undefined : options.find((option) => option.id === editing)} groups={groups} onCancel={() => setEditing(null)} mutate={mutate} />}{options.length === 0 ? <Empty title="No choices yet" text="Add choices after creating an option group." /> : <div className="card-list">{options.map((option) => { const group = groups.find((candidate) => candidate.id === option.group_id); return <article className="resource-card" key={option.id}><div className="resource-main"><span className="number">#{String(option.id).padStart(2, '0')}</span><div><h4>{option.name}</h4><p className="muted">{group?.name ?? 'Unknown group'}</p></div></div><div className="actions"><button className="link-button" onClick={() => setEditing(option.id)}>Edit</button><button className="link-button danger-text" onClick={() => { if (confirm(`Delete ${option.name}?`)) void mutate(() => request<void>(`/options/${option.id}`, { method: 'DELETE' }), 'Choice deleted') }}>Delete</button></div></article> })}</div>}</section>
}

function OptionForm({ option, groups, onCancel, mutate }: { option?: Option; groups: OptionGroup[]; onCancel: () => void; mutate: Mutate }) {
  const [name, setName] = useState(option?.name ?? '')
  const [groupId, setGroupId] = useState(String(option?.group_id ?? groups[0]?.id ?? ''))
  const submit = (event: FormEvent) => { event.preventDefault(); void mutate(async () => { await request<Option>(option ? `/options/${option.id}` : '/options', { method: option ? 'PATCH' : 'POST', body: JSON.stringify({ name: name.trim(), group_id: Number(groupId) }) }); onCancel() }, option ? 'Choice updated' : 'Choice added') }
  return <form className="form-card compact" onSubmit={submit}><div className="form-heading"><div><p className="eyebrow">{option ? 'Edit choice' : 'New choice'}</p><h3>{option ? option.name : 'Add a choice'}</h3></div><button type="button" className="close" onClick={onCancel}>×</button></div>{groups.length === 0 ? <p className="muted">Create an option group first.</p> : <><label>Choice name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Extra cheese" /></label><label>Option group<select required value={groupId} onChange={(event) => setGroupId(event.target.value)}>{groups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</select></label></>}<div className="form-actions"><button type="button" className="button ghost" onClick={onCancel}>Cancel</button><button className="button primary" type="submit" disabled={groups.length === 0}>Save choice</button></div></form>
}

function Empty({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><div className="empty-icon">＋</div><h4>{title}</h4><p className="muted">{text}</p></div>
}

export default App
