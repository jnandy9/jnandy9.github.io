import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import { createContext, useCallback, useContext, useState } from 'react'
import NewInvoice from './pages/NewInvoice.jsx'
import History from './pages/History.jsx'
import Receivers from './pages/Receivers.jsx'
import Settings from './pages/Settings.jsx'

const ToastCtx = createContext(() => {})
export const useToast = () => useContext(ToastCtx)

const tabs = [
  { to: '/new', label: 'New', icon: '＋' },
  { to: '/history', label: 'History', icon: '≣' },
  { to: '/receivers', label: 'Parties', icon: '👥' },
  { to: '/settings', label: 'Business', icon: '⚙' },
]

export default function App() {
  const [toast, setToast] = useState(null)
  const notify = useCallback((msg, type = 'ok') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2600)
  }, [])

  return (
    <ToastCtx.Provider value={notify}>
      <div className="mx-auto flex min-h-screen max-w-md flex-col bg-paper">
        <header className="sticky top-0 z-20 border-b border-hairline bg-ink px-4 py-3 text-white">
          <div className="text-[15px] font-bold tracking-wide">
            SHIVAM ENGINEERING <span className="text-brass-soft">· Billing</span>
          </div>
        </header>

        <main className="flex-1 px-4 pb-28 pt-4">
          <Routes>
            <Route path="/" element={<Navigate to="/new" replace />} />
            <Route path="/new" element={<NewInvoice />} />
            <Route path="/new/:id" element={<NewInvoice />} />
            <Route path="/history" element={<History />} />
            <Route path="/receivers" element={<Receivers />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>

        <nav className="fixed inset-x-0 bottom-0 z-20 mx-auto flex max-w-md border-t border-hairline bg-card/95 backdrop-blur pb-[env(safe-area-inset-bottom)]">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-semibold ${
                  isActive ? 'text-brass' : 'text-ink-soft'
                }`
              }
            >
              <span className="text-lg leading-none">{t.icon}</span>
              {t.label}
            </NavLink>
          ))}
        </nav>

        {toast && (
          <div
            className={`fixed bottom-24 left-1/2 z-30 -translate-x-1/2 rounded-full px-4 py-2 text-sm font-medium text-white shadow-lg ${
              toast.type === 'error' ? 'bg-red' : 'bg-ink'
            }`}
          >
            {toast.msg}
          </div>
        )}
      </div>
    </ToastCtx.Provider>
  )
}
