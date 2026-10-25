import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { Stat } from './components/Shared'
import { GroupsPanel } from './features/menu/GroupsPanel'
import { ItemsPanel } from './features/menu/ItemsPanel'
import { OptionsPanel } from './features/menu/OptionsPanel'
import { pagePath, request } from './features/menu/api'
import type { Item, Mutate, Option, OptionGroup, Page, Pagination, Tab } from './features/menu/types'

const PAGE_SIZE = 5
const emptyPagination: Pagination = { page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 }

function App() {
  const [tab, setTab] = useState<Tab>('items')
  const [items, setItems] = useState<Page<Item[]> | null>(null)
  const [groups, setGroups] = useState<Page<OptionGroup[]> | null>(null)
  const [options, setOptions] = useState<Page<Option[]> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = useCallback(async (
    itemPage = 1,
    groupPage = 1,
    optionPage = 1,
  ) => {
    setLoading(true)
    setError('')
    try {
      const [loadedItems, loadedGroups, loadedOptions] = await Promise.all([
        request<{ items: Item[]; pagination: Pagination }>(pagePath('/items', itemPage, PAGE_SIZE)),
        request<{ groups: OptionGroup[]; pagination: Pagination }>(pagePath('/option-groups', groupPage, PAGE_SIZE)),
        request<{ options: Option[]; pagination: Pagination }>(pagePath('/options', optionPage, PAGE_SIZE)),
      ])
      setItems({ data: loadedItems.items, pagination: loadedItems.pagination })
      setGroups({ data: loadedGroups.groups, pagination: loadedGroups.pagination })
      setOptions({ data: loadedOptions.options, pagination: loadedOptions.pagination })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load menu data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const initialLoad = async () => {
      await load()
    }
    void initialLoad()
  }, [load])

  const mutate: Mutate = async (action, message) => {
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
          <Stat label="Dishes" value={items?.pagination.total ?? 0} />
          <Stat label="Groups" value={groups?.pagination.total ?? 0} />
          <Stat label="Choices" value={options?.pagination.total ?? 0} />
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
            <span>{value === 'items' ? items?.pagination.total ?? 0 : value === 'groups' ? groups?.pagination.total ?? 0 : options?.pagination.total ?? 0}</span>
          </button>
        ))}
      </nav>

      {loading ? (
        <div className="empty-state"><span className="loader" /> Loading your menu...</div>
      ) : tab === 'items' ? (
        <ItemsPanel items={items?.data ?? []} groups={groups?.data ?? []} options={options?.data ?? []} pagination={items?.pagination ?? emptyPagination} onPageChange={(page) => void load(page, groups?.pagination.page, options?.pagination.page)} mutate={mutate} />
      ) : tab === 'groups' ? (
        <GroupsPanel groups={groups?.data ?? []} pagination={groups?.pagination ?? emptyPagination} onPageChange={(page) => void load(items?.pagination.page, page, options?.pagination.page)} mutate={mutate} />
      ) : (
        <OptionsPanel groups={groups?.data ?? []} options={options?.data ?? []} pagination={options?.pagination ?? emptyPagination} onPageChange={(page) => void load(items?.pagination.page, groups?.pagination.page, page)} mutate={mutate} />
      )}
    </main>
  )
}

export default App
