import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import './App.css'
import { Stat } from './components/Shared'
import { GroupsPanel } from './features/menu/GroupsPanel'
import { ItemsPanel } from './features/menu/ItemsPanel'
import { OptionsPanel } from './features/menu/OptionsPanel'
import { pagePath, request as menuRequest } from './features/menu/api'
import { OrderPage } from './features/orders/OrderPage'
import { OrdersPanel } from './features/orders/OrdersPanel'
import { request as orderRequest, type Order } from './features/orders/api'
import { listTables, type Table } from './features/tables/api'
import { TablePanel } from './features/tables/TablePanel'
import type { Item, Mutate, Option, OptionGroup, Page, Pagination, Tab } from './features/menu/types'

const PAGE_SIZE = 5
const emptyPagination: Pagination = { page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 }

function navigate(path: string) {
  window.history.pushState({}, '', path)
  window.dispatchEvent(new PopStateEvent('popstate'))
}

function App() {
  const [path, setPath] = useState(window.location.pathname)
  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  return path.startsWith('/order') ? <CustomerShell /> : <AdminShell />
}

function Shell({ children, customer = false }: { children: ReactNode; customer?: boolean }) {
  return <main className="shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark">R</span><div><p className="eyebrow">{customer ? 'Restaurant ordering' : 'Restaurant admin'}</p><h1>{customer ? 'Place an order' : 'Restaurant studio'}</h1></div></div>
      <button className="button ghost" onClick={() => navigate(customer ? '/admin' : '/order')}>{customer ? 'Admin' : 'Customer order'}</button>
    </header>
    {children}
  </main>
}

function CustomerShell() {
  return <Shell customer><OrderPage onBack={() => navigate('/admin')} /></Shell>
}

function AdminShell() {
  const [tab, setTab] = useState<Tab | 'tables'>('items')
  const [items, setItems] = useState<Page<Item[]> | null>(null)
  const [groups, setGroups] = useState<Page<OptionGroup[]> | null>(null)
  const [options, setOptions] = useState<Page<Option[]> | null>(null)
  const [tables, setTables] = useState<Table[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = useCallback(async (itemPage = 1, groupPage = 1, optionPage = 1) => {
    setLoading(true)
    setError('')
    try {
      const [loadedItems, loadedGroups, loadedOptions, loadedTables, loadedOrders] = await Promise.all([
        menuRequest<{ items: Item[]; pagination: Pagination }>(pagePath('/items', itemPage, PAGE_SIZE)),
        menuRequest<{ groups: OptionGroup[]; pagination: Pagination }>(pagePath('/option-groups', groupPage, PAGE_SIZE)),
        menuRequest<{ options: Option[]; pagination: Pagination }>(pagePath('/options', optionPage, PAGE_SIZE)),
        listTables(),
        orderRequest<Order[]>('/api/admin/orders'),
      ])
      setItems({ data: loadedItems.items, pagination: loadedItems.pagination })
      setGroups({ data: loadedGroups.groups, pagination: loadedGroups.pagination })
      setOptions({ data: loadedOptions.options, pagination: loadedOptions.pagination })
      setTables(loadedTables)
      setOrders(loadedOrders)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load admin data')
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

  return <Shell>
    <section className="intro"><div><p className="eyebrow accent">Admin workspace</p><h2>Manage your restaurant.</h2><p className="muted">Maintain tables, dishes, orders, and choices.</p></div><div className="stats"><Stat label="Dishes" value={items?.pagination.total ?? 0} /><Stat label="Tables" value={tables.length} /><Stat label="Open orders" value={orders.length} /></div></section>
    {error && <div className="alert error">{error}</div>}
    {notice && <div className="alert success">{notice}</div>}
    <nav className="tabs" aria-label="Admin resources">{(['items', 'groups', 'options', 'tables', 'orders'] as const).map((value) => <button key={value} className={tab === value ? 'tab active' : 'tab'} onClick={() => setTab(value)}>{value === 'items' ? 'Dishes' : value === 'groups' ? 'Option groups' : value === 'options' ? 'Choices' : value === 'tables' ? 'Tables' : 'Orders'}<span>{value === 'items' ? items?.pagination.total ?? 0 : value === 'groups' ? groups?.pagination.total ?? 0 : value === 'options' ? options?.pagination.total ?? 0 : value === 'tables' ? tables.length : orders.length}</span></button>)}</nav>
    {loading ? <div className="empty-state"><span className="loader" /> Loading admin data...</div> : tab === 'orders' ? <OrdersPanel orders={orders} onChange={setOrders} /> : tab === 'tables' ? <TablePanel tables={tables} orders={orders} onChange={setTables} /> : tab === 'items' ? <ItemsPanel items={items?.data ?? []} groups={groups?.data ?? []} options={options?.data ?? []} pagination={items?.pagination ?? emptyPagination} onPageChange={(page) => void load(page, groups?.pagination.page, options?.pagination.page)} mutate={mutate} /> : tab === 'groups' ? <GroupsPanel groups={groups?.data ?? []} pagination={groups?.pagination ?? emptyPagination} onPageChange={(page) => void load(items?.pagination.page, page, options?.pagination.page)} mutate={mutate} /> : <OptionsPanel groups={groups?.data ?? []} options={options?.data ?? []} pagination={options?.pagination ?? emptyPagination} onPageChange={(page) => void load(items?.pagination.page, groups?.pagination.page, page)} mutate={mutate} />}
  </Shell>
}

export default App
