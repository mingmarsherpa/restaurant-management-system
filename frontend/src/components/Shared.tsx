export function Stat({ label, value }: { label: string; value: number }) {
  return <div className="stat"><strong>{value.toString().padStart(2, '0')}</strong><span>{label}</span></div>
}

export function Empty({ title, text }: { title: string; text: string }) {
  return <div className="empty-state"><div className="empty-icon">＋</div><h4>{title}</h4><p className="muted">{text}</p></div>
}

export function PaginationControls({
  page,
  totalPages,
  onPageChange,
}: {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  if (totalPages <= 1) return null
  return <div className="pagination" aria-label="Pagination">
    <button className="button ghost" disabled={page === 1} onClick={() => onPageChange(page - 1)}>Previous</button>
    <span className="muted">Page {page} of {totalPages}</span>
    <button className="button ghost" disabled={page === totalPages} onClick={() => onPageChange(page + 1)}>Next</button>
  </div>
}
