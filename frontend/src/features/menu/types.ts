export type Tab = 'items' | 'groups' | 'options' | 'orders'

export type Option = { id: number; name: string; group_id: number }
export type OptionGroup = { id: number; name: string; options: Option[] }
export type ItemOptionPrice = { option_id: number; extra_price_paisa: number }
export type Item = {
  id: number
  name: string
  base_price_paisa: number
  option_groups: OptionGroup[]
  item_options: ItemOptionPrice[]
}

export type Pagination = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type Page<T> = {
  data: T
  pagination: Pagination
}

export type Mutate = (action: () => Promise<void>, message: string) => Promise<void>
