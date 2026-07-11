const BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

async function req(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res
}

export const api = {
  base: BASE,

  // settings (business profile)
  getSettings: () => req('/settings'),
  saveSettings: (body) => req('/settings', { method: 'PUT', body: JSON.stringify(body) }),

  // receivers (saved customers)
  listReceivers: () => req('/receivers'),
  createReceiver: (body) => req('/receivers', { method: 'POST', body: JSON.stringify(body) }),
  updateReceiver: (id, body) => req(`/receivers/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteReceiver: (id) => req(`/receivers/${id}`, { method: 'DELETE' }),

  // goods catalogue
  listGoods: () => req('/goods'),

  // sessions (financial-year folders)
  listSessions: () => req('/sessions'),
  createSession: (name) => req('/sessions', { method: 'POST', body: JSON.stringify({ name }) }),
  deleteSession: (name) => req(`/sessions/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  // invoices
  listInvoices: (session) => req('/invoices' + (session ? `?session=${encodeURIComponent(session)}` : '')),
  createInvoice: (body) => req('/invoices', { method: 'POST', body: JSON.stringify(body) }),
  updateInvoice: (id, body) => req(`/invoices/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  getInvoice: (id) => req(`/invoices/${id}`),
  deleteInvoice: (id) => req(`/invoices/${id}`, { method: 'DELETE' }),
  pdfUrl: (id) => `${BASE}/invoices/${id}/pdf`,

  // Download the PDF as "<company> <bill no>.pdf" instead of opening a tab.
  downloadPdf: async (inv) => {
    const res = await fetch(`${BASE}/invoices/${inv.id}/pdf`)
    if (!res.ok) throw new Error('Could not download PDF')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = pdfFilename(inv)
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1500)
  },
}

export function pdfFilename(inv) {
  const buyer = (inv.buyer?.name || 'Invoice').trim()
  const serial = (inv.invoice_no || '').split('/')[0].trim()
  const name = `${buyer} ${serial}`.replace(/[\\/:*?"<>|]+/g, '').trim() || 'Invoice'
  return `${name}.pdf`
}

export function money(n) {
  const v = Number(n || 0)
  return v.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
