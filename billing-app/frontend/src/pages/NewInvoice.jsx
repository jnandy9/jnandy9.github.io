import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, money } from '../api.js'
import { useToast } from '../App.jsx'

// Two bill types, each tied to an HSN/SAC code.
const HSN_NORMAL = '84833'
const HSN_MACHINING = '998931'
const HSN_OPTIONS = [HSN_NORMAL, HSN_MACHINING]
const BILL_TYPES = {
  NORMAL: { label: 'Normal (goods)', hsn: HSN_NORMAL },
  MACHINING: { label: 'Machining Charges Only', hsn: HSN_MACHINING },
}
const SELLER_CODE = 'SEC' // Shivam Engineering Concern — the middle token of the invoice no.

// Invoice No. is composed as  <serial>/SEC/<session>  e.g. 02/SEC/2026-27
const composeNo = (serial, session) =>
  serial && session ? `${serial}/${SELLER_CODE}/${session}` : serial || ''
const parseNo = (full) => {
  const m = (full || '').match(new RegExp(`^(.*)/${SELLER_CODE}/(.+)$`))
  return m ? { serial: m[1], session: m[2] } : { serial: full || '', session: '' }
}

const emptyParty = () => ({ name: '', address: '', state: 'WEST BENGAL', state_code: '19', gstin: '' })
const emptyItem = (hsn = HSN_NORMAL) => ({ hsn, description: '', qty: 1, rate: 0 })
const todayISO = () => new Date().toISOString().slice(0, 10)

const newDraft = () => ({
  order_no: '', date: todayISO(), cnrr_no: '', mode_of_transport: '', through: '',
  bill_type: 'NORMAL',
  buyer: emptyParty(), consignee: emptyParty(), same_as_buyer: true,
  items: [emptyItem(HSN_NORMAL)],
  tax_mode: 'SGST_CGST', sgst_pct: 9, cgst_pct: 9, igst_pct: 18, other_charges: 0,
})

function compute(d) {
  const items = d.items.map((it) => ({ ...it, amount: (Number(it.qty) || 0) * (Number(it.rate) || 0) }))
  const subtotal = items.reduce((s, i) => s + i.amount, 0)
  const other = Number(d.other_charges) || 0
  let sgst = 0, cgst = 0, igst = 0
  if (d.tax_mode === 'IGST') igst = (subtotal * (Number(d.igst_pct) || 0)) / 100
  else { sgst = (subtotal * (Number(d.sgst_pct) || 0)) / 100; cgst = (subtotal * (Number(d.cgst_pct) || 0)) / 100 }
  return { items, subtotal, other, sgst, cgst, igst, grand: subtotal + other + sgst + cgst + igst }
}

function PartyForm({ party, onChange }) {
  const set = (k, v) => onChange({ ...party, [k]: v })
  return (
    <div className="space-y-3">
      <div>
        <label className="field-label">Name</label>
        <input className="field-input" value={party.name} onChange={(e) => set('name', e.target.value)}
          placeholder="Party / business name" />
      </div>
      <div>
        <label className="field-label">Address</label>
        <textarea className="field-input" rows={2} value={party.address}
          onChange={(e) => set('address', e.target.value)} placeholder="Street, city, PIN" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="field-label">State</label>
          <input className="field-input" value={party.state} onChange={(e) => set('state', e.target.value)} />
        </div>
        <div>
          <label className="field-label">State code</label>
          <input className="field-input" value={party.state_code} onChange={(e) => set('state_code', e.target.value)} />
        </div>
      </div>
      <div>
        <label className="field-label">GSTIN / Unique ID</label>
        <input className="field-input" value={party.gstin} onChange={(e) => set('gstin', e.target.value)} />
      </div>
    </div>
  )
}

export default function NewInvoice() {
  const notify = useToast()
  const navigate = useNavigate()
  const { id: editId } = useParams()
  const [draft, setDraft] = useState(newDraft)
  const [serial, setSerial] = useState('')
  const [session, setSession] = useState(() => localStorage.getItem('activeSession') || '')
  const [sessions, setSessions] = useState([])
  const [creatingSession, setCreatingSession] = useState(false)
  const [newSession, setNewSession] = useState('')
  const [receivers, setReceivers] = useState([])
  const [goods, setGoods] = useState([])
  const [saving, setSaving] = useState(false)
  const calc = useMemo(() => compute(draft), [draft])
  const invoiceNo = composeNo(serial, session)

  const loadLists = () => {
    api.listReceivers().then(setReceivers).catch(() => {})
    api.listGoods().then(setGoods).catch(() => {})
    api.listSessions().then((ss) => {
      setSessions(ss)
      setSession((cur) => cur || (ss[0] && ss[0].name) || '')
    }).catch(() => {})
  }
  useEffect(loadLists, [])

  // Load an existing invoice when editing (route /new/:id).
  useEffect(() => {
    if (!editId) { setDraft(newDraft()); setSerial(''); return }
    api.getInvoice(editId)
      .then((inv) => {
        const bill_type = inv.bill_type || (inv.items?.[0]?.hsn === HSN_MACHINING ? 'MACHINING' : 'NORMAL')
        setDraft({
          ...newDraft(), ...inv, bill_type,
          items: inv.items?.length ? inv.items : [emptyItem(BILL_TYPES[bill_type].hsn)],
          consignee: inv.consignee || emptyParty(),
        })
        const parsed = parseNo(inv.invoice_no)
        setSerial(parsed.serial)
        setSession(inv.session || parsed.session || '')
      })
      .catch((e) => notify(e.message || 'Could not load invoice', 'error'))
  }, [editId])

  const set = (patch) => setDraft((d) => ({ ...d, ...patch }))
  const setBuyer = (buyer) => setDraft((d) => ({ ...d, buyer, consignee: d.same_as_buyer ? buyer : d.consignee }))
  const setItem = (i, patch) =>
    setDraft((d) => ({ ...d, items: d.items.map((it, idx) => (idx === i ? { ...it, ...patch } : it)) }))
  const addItem = () => setDraft((d) => ({ ...d, items: [...d.items, emptyItem(BILL_TYPES[d.bill_type].hsn)] }))
  const removeItem = (i) =>
    setDraft((d) => ({ ...d, items: d.items.length > 1 ? d.items.filter((_, idx) => idx !== i) : d.items }))
  const setBillType = (type) =>
    setDraft((d) => ({ ...d, bill_type: type, items: d.items.map((it) => ({ ...it, hsn: BILL_TYPES[type].hsn })) }))

  const chooseSession = (name) => {
    setSession(name)
    if (name) localStorage.setItem('activeSession', name)
  }
  const createSession = async () => {
    const name = newSession.trim()
    if (!name) return
    try {
      await api.createSession(name)
      await api.listSessions().then(setSessions)
      chooseSession(name)
      setNewSession(''); setCreatingSession(false)
      notify(`Session ${name} created`)
    } catch (e) { notify(e.message, 'error') }
  }

  const loadReceiver = (id) => {
    const r = receivers.find((x) => x.id === id)
    if (!r) return
    setBuyer({ name: r.name, address: r.address, state: r.state, state_code: r.state_code, gstin: r.gstin })
    notify('Party loaded')
  }
  const pickGood = (i, desc) => {
    const g = goods.find((x) => x.description === desc)
    if (g) setItem(i, { description: g.description, hsn: g.hsn || draft.items[i].hsn, rate: g.rate })
    else setItem(i, { description: desc })
  }

  const canSave = serial.trim() && session.trim() && draft.buyer.name.trim() && draft.items.some((i) => i.description.trim())

  const save = async () => {
    setSaving(true)
    try {
      const body = {
        ...draft,
        invoice_no: invoiceNo, challan_no: invoiceNo, session,
        consignee: draft.same_as_buyer ? draft.buyer : draft.consignee,
      }
      const inv = editId ? await api.updateInvoice(editId, body) : await api.createInvoice(body)
      notify(editId ? 'Invoice updated' : 'Invoice saved')
      window.open(api.pdfUrl(inv.id), '_blank')
      loadLists()
      if (editId) navigate('/history')
      else { setDraft(newDraft()); setSerial('') }
    } catch (e) {
      notify(e.message || 'Save failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-ink">{editId ? 'Edit invoice' : 'New invoice'}</h1>

      {/* Session */}
      <section className="card space-y-3">
        <div className="section-title">Session (financial year)</div>
        {!creatingSession ? (
          <div className="flex gap-2">
            <select className="field-input" value={session} onChange={(e) => chooseSession(e.target.value)}>
              {sessions.length === 0 && <option value="">— create a session —</option>}
              {sessions.map((s) => (<option key={s.name} value={s.name}>{s.name}</option>))}
            </select>
            <button className="btn-outline whitespace-nowrap" onClick={() => setCreatingSession(true)}>+ New</button>
          </div>
        ) : (
          <div className="flex gap-2">
            <input className="field-input" autoFocus placeholder="e.g. 2026-27" value={newSession}
              onChange={(e) => setNewSession(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && createSession()} />
            <button className="btn-primary whitespace-nowrap" onClick={createSession}>Create</button>
            <button className="btn-outline" onClick={() => { setCreatingSession(false); setNewSession('') }}>✕</button>
          </div>
        )}
        <p className="text-xs text-ink-soft">Invoices are filed under this session. It becomes the year in the invoice number.</p>
      </section>

      {/* Bill type */}
      <section className="card space-y-3">
        <div className="section-title">Bill type</div>
        <div className="flex gap-2">
          {Object.entries(BILL_TYPES).map(([key, v]) => (
            <button key={key}
              className={`btn flex-1 flex-col !items-start py-2.5 ${draft.bill_type === key ? 'bg-brass-soft text-brass' : 'border border-hairline bg-white text-ink-soft'}`}
              onClick={() => setBillType(key)}>
              <span className="text-sm font-semibold">{v.label}</span>
              <span className="text-[11px] opacity-80">HSN/SAC {v.hsn}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Invoice details */}
      <section className="card space-y-3">
        <div className="section-title">Invoice details</div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="field-label">Invoice serial No.</label>
            <input className="field-input" value={serial} onChange={(e) => setSerial(e.target.value)} placeholder="02" />
          </div>
          <div>
            <label className="field-label">Date</label>
            <input type="date" className="field-input" value={draft.date}
              onChange={(e) => set({ date: e.target.value })} />
          </div>
        </div>
        <div className="rounded-lg bg-paper px-3 py-2 text-sm">
          <span className="text-ink-soft">Invoice No.: </span>
          <span className="font-semibold text-ink">{invoiceNo || '—'}</span>
          <span className="text-ink-soft"> (Challan No. same)</span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="field-label">Order No.</label>
            <input className="field-input" value={draft.order_no}
              onChange={(e) => set({ order_no: e.target.value })} />
          </div>
          <div>
            <label className="field-label">Mode of transport</label>
            <input className="field-input" value={draft.mode_of_transport}
              onChange={(e) => set({ mode_of_transport: e.target.value })} placeholder="ENGING VAN" />
          </div>
        </div>
      </section>

      {/* Receiver */}
      <section className="card space-y-3">
        <div className="section-title">Details of receiver (Billed to)</div>
        {receivers.length > 0 && (
          <div>
            <label className="field-label">Load a saved party</label>
            <select className="field-input" value="" onChange={(e) => loadReceiver(e.target.value)}>
              <option value="">— Select saved party —</option>
              {receivers.map((r) => (<option key={r.id} value={r.id}>{r.name}</option>))}
            </select>
          </div>
        )}
        <PartyForm party={draft.buyer} onChange={setBuyer} />
        <label className="flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" checked={draft.same_as_buyer}
            onChange={(e) => setDraft((d) => ({ ...d, same_as_buyer: e.target.checked, consignee: e.target.checked ? d.buyer : d.consignee }))} />
          Consignee (shipped to) same as receiver
        </label>
        {!draft.same_as_buyer && (
          <div className="border-t border-hairline pt-3">
            <div className="section-title mb-2">Details of consignee (Shipped to)</div>
            <PartyForm party={draft.consignee} onChange={(c) => setDraft((d) => ({ ...d, consignee: c }))} />
          </div>
        )}
      </section>

      {/* Goods */}
      <section className="card space-y-3">
        <div className="section-title">Goods &amp; amounts</div>
        <datalist id="goods-list">
          {goods.map((g) => (<option key={g.id} value={g.description} />))}
        </datalist>
        {draft.items.map((it, i) => (
          <div key={i} className="rounded-xl border border-hairline p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-ink-soft">Item {i + 1}</span>
              {draft.items.length > 1 && (
                <button className="text-red text-sm" onClick={() => removeItem(i)}>Remove</button>
              )}
            </div>
            <input className="field-input" list="goods-list" value={it.description}
              onChange={(e) => pickGood(i, e.target.value)} placeholder="Description of goods" />
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="field-label">HSN/SAC</label>
                <select className="field-input" value={HSN_OPTIONS.includes(it.hsn) ? it.hsn : HSN_NORMAL}
                  onChange={(e) => setItem(i, { hsn: e.target.value })}>
                  {HSN_OPTIONS.map((h) => (<option key={h} value={h}>{h}</option>))}
                </select>
              </div>
              <div>
                <label className="field-label">Qty</label>
                <input type="number" inputMode="decimal" className="field-input" value={it.qty}
                  onChange={(e) => setItem(i, { qty: e.target.value })} />
              </div>
              <div>
                <label className="field-label">Rate ₹</label>
                <input type="number" inputMode="decimal" className="field-input" value={it.rate}
                  onChange={(e) => setItem(i, { rate: e.target.value })} />
              </div>
            </div>
            <div className="text-right text-sm text-ink-soft">
              Amount: <span className="font-semibold text-ink">₹ {money((Number(it.qty) || 0) * (Number(it.rate) || 0))}</span>
            </div>
          </div>
        ))}
        <button className="btn-outline w-full" onClick={addItem}>+ Add item</button>
      </section>

      {/* Tax + totals */}
      <section className="card space-y-3">
        <div className="section-title">Tax &amp; totals</div>
        <div className="flex gap-2">
          <button className={`btn flex-1 ${draft.tax_mode === 'SGST_CGST' ? 'bg-brass-soft text-brass' : 'border border-hairline bg-white text-ink-soft'}`}
            onClick={() => set({ tax_mode: 'SGST_CGST' })}>SGST + CGST</button>
          <button className={`btn flex-1 ${draft.tax_mode === 'IGST' ? 'bg-brass-soft text-brass' : 'border border-hairline bg-white text-ink-soft'}`}
            onClick={() => set({ tax_mode: 'IGST' })}>IGST</button>
        </div>
        {draft.tax_mode === 'SGST_CGST' ? (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="field-label">SGST %</label>
              <input type="number" className="field-input" value={draft.sgst_pct} onChange={(e) => set({ sgst_pct: e.target.value })} />
            </div>
            <div>
              <label className="field-label">CGST %</label>
              <input type="number" className="field-input" value={draft.cgst_pct} onChange={(e) => set({ cgst_pct: e.target.value })} />
            </div>
          </div>
        ) : (
          <div>
            <label className="field-label">IGST %</label>
            <input type="number" className="field-input" value={draft.igst_pct} onChange={(e) => set({ igst_pct: e.target.value })} />
          </div>
        )}

        <div className="rounded-xl bg-paper p-3 text-sm">
          <Row label="Subtotal" value={calc.subtotal} />
          {draft.tax_mode === 'SGST_CGST' ? (
            <>
              <Row label={`SGST @ ${draft.sgst_pct}%`} value={calc.sgst} />
              <Row label={`CGST @ ${draft.cgst_pct}%`} value={calc.cgst} />
            </>
          ) : (
            <Row label={`IGST @ ${draft.igst_pct}%`} value={calc.igst} />
          )}
          <div className="mt-2 flex justify-between border-t border-hairline pt-2 text-base font-bold text-ink">
            <span>Grand total</span><span>₹ {money(calc.grand)}</span>
          </div>
        </div>
      </section>

      <div className="flex gap-2">
        {editId && (
          <button className="btn-outline flex-1 py-3" onClick={() => navigate('/history')}>Cancel</button>
        )}
        <button className="btn-primary flex-[2] py-3 text-base" disabled={!canSave || saving} onClick={save}>
          {saving ? 'Saving…' : editId ? 'Update & generate PDF' : 'Save & generate PDF'}
        </button>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between py-0.5 text-ink-soft">
      <span>{label}</span><span className="text-ink">₹ {money(value)}</span>
    </div>
  )
}
