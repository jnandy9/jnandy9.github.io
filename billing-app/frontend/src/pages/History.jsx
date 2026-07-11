import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, money } from '../api.js'
import { useToast } from '../App.jsx'

const fmtDate = (iso) => {
  if (!iso || !iso.includes('-')) return iso || ''
  const [y, m, d] = iso.split('-')
  return `${d}-${m}-${y}`
}

export default function History() {
  const notify = useToast()
  const navigate = useNavigate()
  const [invoices, setInvoices] = useState([])
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(() => localStorage.getItem('activeSession') || '')
  const [loading, setLoading] = useState(true)
  const [confirmId, setConfirmId] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([api.listInvoices(), api.listSessions()])
      .then(([inv, ss]) => { setInvoices(inv); setSessions(ss) })
      .catch((e) => notify(e.message, 'error'))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const del = async (id) => {
    try {
      await api.deleteInvoice(id)
      setConfirmId(null)
      setInvoices((prev) => prev.filter((x) => x.id !== id))
      notify('Invoice deleted')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const shown = activeSession ? invoices.filter((i) => i.session === activeSession) : invoices
  const chips = ['', ...sessions.map((s) => s.name)]

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-ink">History</h1>

      {/* Session folders */}
      <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1">
        {chips.map((name) => (
          <button key={name || 'all'}
            onClick={() => setActiveSession(name)}
            className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-sm font-semibold ${
              activeSession === name ? 'border-brass bg-brass-soft text-brass' : 'border-hairline bg-white text-ink-soft'
            }`}>
            {name ? `📁 ${name}` : 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-ink-soft">Loading…</p>
      ) : shown.length === 0 ? (
        <div className="card text-center text-ink-soft">
          <p className="font-semibold text-ink">No invoices {activeSession ? `in ${activeSession}` : 'yet'}</p>
          <p className="text-sm">Saved invoices appear here, filed by session.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {shown.map((inv) => (
            <div key={inv.id} className="card">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate font-semibold text-ink">{inv.buyer?.name || '—'}</div>
                  <div className="text-xs text-ink-soft">
                    {inv.invoice_no} · {fmtDate(inv.date)}
                    {inv.bill_type === 'MACHINING' && <span className="ml-1 text-brass">· Machining</span>}
                  </div>
                </div>
                <div className="whitespace-nowrap text-right font-bold text-ink">
                  ₹ {money(inv.totals?.grand_total)}
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button className="btn-brass flex-1"
                  onClick={() => api.downloadPdf(inv).catch((e) => notify(e.message, 'error'))}>
                  Download PDF
                </button>
                <button className="btn-outline" onClick={() => navigate(`/new/${inv.id}`)}>Edit</button>
                <button className="btn-outline text-red" onClick={() => setConfirmId(inv.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {confirmId && (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-black/40 px-6"
          onClick={() => setConfirmId(null)}>
          <div className="w-full max-w-sm rounded-2xl bg-white p-5" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-ink">Delete invoice?</h3>
            <p className="mt-1 text-sm text-ink-soft">This permanently removes it from history.</p>
            <div className="mt-4 flex justify-end gap-2">
              <button className="btn-outline" onClick={() => setConfirmId(null)}>Cancel</button>
              <button className="btn bg-red text-white" onClick={() => del(confirmId)}>Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
