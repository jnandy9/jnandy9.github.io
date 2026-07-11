import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useToast } from '../App.jsx'

const empty = () => ({ name: '', address: '', state: 'WEST BENGAL', state_code: '19', gstin: '' })

export default function Receivers() {
  const notify = useToast()
  const [list, setList] = useState([])
  const [editing, setEditing] = useState(null) // {id?, ...party}
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.listReceivers().then(setList).catch((e) => notify(e.message, 'error')).finally(() => setLoading(false))
  }
  useEffect(load, [])

  const save = async () => {
    try {
      const { id, ...body } = editing
      if (id) await api.updateReceiver(id, body)
      else await api.createReceiver(body)
      setEditing(null)
      notify('Party saved')
      load()
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const del = async (id) => {
    try { await api.deleteReceiver(id); notify('Deleted'); load() }
    catch (e) { notify(e.message, 'error') }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-ink">Saved parties</h1>
        <button className="btn-primary" onClick={() => setEditing(empty())}>+ Add</button>
      </div>

      {loading ? (
        <p className="text-ink-soft">Loading…</p>
      ) : list.length === 0 ? (
        <div className="card text-center text-ink-soft">
          <p className="font-semibold text-ink">No saved parties</p>
          <p className="text-sm">Parties are saved automatically when you bill them, or add one here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {list.map((r) => (
            <div key={r.id} className="card">
              <div className="font-semibold text-ink">{r.name}</div>
              <div className="text-sm text-ink-soft">{r.address}</div>
              <div className="mt-1 text-xs text-ink-soft">GSTIN: {r.gstin || '—'} · {r.state} ({r.state_code})</div>
              <div className="mt-3 flex gap-2">
                <button className="btn-outline flex-1" onClick={() => setEditing(r)}>Edit</button>
                <button className="btn-outline text-red" onClick={() => del(r.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-30 flex items-end justify-center bg-black/40 sm:items-center"
          onClick={() => setEditing(null)}>
          <div className="w-full max-w-md rounded-t-2xl bg-white p-5 sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="mb-3 text-lg font-bold text-ink">{editing.id ? 'Edit party' : 'New party'}</h3>
            <div className="space-y-3">
              <div>
                <label className="field-label">Name</label>
                <input className="field-input" value={editing.name}
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </div>
              <div>
                <label className="field-label">Address</label>
                <textarea className="field-input" rows={2} value={editing.address}
                  onChange={(e) => setEditing({ ...editing, address: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="field-label">State</label>
                  <input className="field-input" value={editing.state}
                    onChange={(e) => setEditing({ ...editing, state: e.target.value })} />
                </div>
                <div>
                  <label className="field-label">State code</label>
                  <input className="field-input" value={editing.state_code}
                    onChange={(e) => setEditing({ ...editing, state_code: e.target.value })} />
                </div>
              </div>
              <div>
                <label className="field-label">GSTIN / Unique ID</label>
                <input className="field-input" value={editing.gstin}
                  onChange={(e) => setEditing({ ...editing, gstin: e.target.value })} />
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button className="btn-outline" onClick={() => setEditing(null)}>Cancel</button>
              <button className="btn-primary" disabled={!editing.name.trim()} onClick={save}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
