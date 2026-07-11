import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useToast } from '../App.jsx'

export default function Settings() {
  const notify = useToast()
  const [s, setS] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.getSettings().then(setS).catch((e) => notify(e.message, 'error'))
  }, [])

  if (!s) return <p className="text-ink-soft">Loading…</p>

  const set = (k, v) => setS({ ...s, [k]: v })
  const setBank = (i, k, v) =>
    setS({ ...s, banks: s.banks.map((b, idx) => (idx === i ? { ...b, [k]: v } : b)) })
  const addBank = () => setS({ ...s, banks: [...(s.banks || []), { name: '', ac: '', ifsc: '' }] })
  const removeBank = (i) => setS({ ...s, banks: s.banks.filter((_, idx) => idx !== i) })

  const save = async () => {
    setSaving(true)
    try { await api.saveSettings(s); notify('Business profile saved') }
    catch (e) { notify(e.message, 'error') }
    finally { setSaving(false) }
  }

  const Text = ({ label, k, area }) => (
    <div>
      <label className="field-label">{label}</label>
      {area
        ? <textarea className="field-input" rows={2} value={s[k] || ''} onChange={(e) => set(k, e.target.value)} />
        : <input className="field-input" value={s[k] || ''} onChange={(e) => set(k, e.target.value)} />}
    </div>
  )

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-ink">Business profile</h1>
      <p className="text-sm text-ink-soft">These details print on every invoice. Edit carefully.</p>

      <section className="card space-y-3">
        <div className="section-title">Header</div>
        <Text label="Business name" k="name" />
        <Text label="Tagline" k="tagline" area />
        <Text label="Specialist line" k="specialist" area />
        <Text label="Office &amp; works" k="office" area />
        <div className="grid grid-cols-2 gap-3">
          <Text label="GSTIN" k="gstin" />
          <Text label="PAN" k="pan" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Text label="Mobile" k="mobile" />
          <Text label="State code" k="state_code" />
        </div>
        <Text label="State" k="state" />
      </section>

      <section className="card space-y-3">
        <div className="flex items-center justify-between">
          <div className="section-title">Bank accounts</div>
          <button className="text-sm font-semibold text-brass" onClick={addBank}>+ Add</button>
        </div>
        {(s.banks || []).map((b, i) => (
          <div key={i} className="rounded-xl border border-hairline p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-ink-soft">Bank {i + 1}</span>
              <button className="text-sm text-red" onClick={() => removeBank(i)}>Remove</button>
            </div>
            <input className="field-input" placeholder="Bank name & branch" value={b.name}
              onChange={(e) => setBank(i, 'name', e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              <input className="field-input" placeholder="A/C no." value={b.ac}
                onChange={(e) => setBank(i, 'ac', e.target.value)} />
              <input className="field-input" placeholder="IFSC" value={b.ifsc}
                onChange={(e) => setBank(i, 'ifsc', e.target.value)} />
            </div>
          </div>
        ))}
      </section>

      <button className="btn-primary w-full py-3" disabled={saving} onClick={save}>
        {saving ? 'Saving…' : 'Save business profile'}
      </button>
    </div>
  )
}
