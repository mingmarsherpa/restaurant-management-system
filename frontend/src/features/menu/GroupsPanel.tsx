import { useState } from 'react'
import type { FormEvent } from 'react'
import { Empty, PaginationControls } from '../../components/Shared'
import { request } from './api'
import type { Mutate, OptionGroup, Pagination } from './types'

export function GroupsPanel({ groups, pagination, onPageChange, mutate }: { groups: OptionGroup[]; pagination: Pagination; onPageChange: (page: number) => void; mutate: Mutate }) {
  const [editing, setEditing] = useState<number | 'new' | null>(null)
  return <section className="content-grid"><div className="section-heading"><div><p className="eyebrow">Organize choices</p><h3>Option groups</h3></div><button className="button primary" onClick={() => setEditing('new')}>+ Add group</button></div>{editing !== null && <GroupForm group={editing === 'new' ? undefined : groups.find((group) => group.id === editing)} onCancel={() => setEditing(null)} mutate={mutate} />}{groups.length === 0 ? <Empty title="No option groups yet" text="Create a group like Size, Milk, or Toppings." /> : <div className="group-grid">{groups.map((group) => <article className="resource-card group-card" key={group.id}><div><span className="number">#{String(group.id).padStart(2, '0')}</span><h4>{group.name}</h4><p className="muted">{group.options.length} choice{group.options.length === 1 ? '' : 's'}</p></div><div className="group-options">{group.options.map((option) => <span key={option.id}>{option.name}</span>)}</div><div className="actions"><button className="link-button" onClick={() => setEditing(group.id)}>Edit</button><button className="link-button danger-text" onClick={() => { if (confirm(`Delete ${group.name}?`)) void mutate(() => request<void>(`/option-groups/${group.id}`, { method: 'DELETE' }), 'Option group deleted') }}>Delete</button></div></article>)}</div>}<PaginationControls page={pagination.page} totalPages={pagination.total_pages} onPageChange={onPageChange} /></section>
}

function GroupForm({ group, onCancel, mutate }: { group?: OptionGroup; onCancel: () => void; mutate: Mutate }) {
  const [name, setName] = useState(group?.name ?? '')
  const submit = (event: FormEvent) => { event.preventDefault(); void mutate(async () => { await request<OptionGroup>(group ? `/option-groups/${group.id}` : '/option-groups', { method: group ? 'PATCH' : 'POST', body: JSON.stringify(group ? { name: name.trim() } : { name: name.trim(), options: [] }) }); onCancel() }, group ? 'Option group updated' : 'Option group added') }
  return <form className="form-card compact" onSubmit={submit}><div className="form-heading"><div><p className="eyebrow">{group ? 'Edit group' : 'New group'}</p><h3>{group ? group.name : 'Add an option group'}</h3></div><button type="button" className="close" onClick={onCancel}>×</button></div><label>Group name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Toppings" /></label><div className="form-actions"><button type="button" className="button ghost" onClick={onCancel}>Cancel</button><button className="button primary" type="submit">Save group</button></div></form>
}
