import { useState, useRef, useEffect } from 'react'
import { NavLink, Outlet } from 'react-router'

const navItems = [
  {
    to: '/',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    to: '/records',
    label: 'Records',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h6m-6 4h6" />
      </svg>
    ),
  },
  {
    to: '/upload',
    label: 'Upload',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
      </svg>
    ),
  },
  {
    to: '/analysis',
    label: 'Analysis',
    icon: (
      <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
]

export default function AppLayout() {
  const [searchOpen, setSearchOpen] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const sidebarRef = useRef<HTMLElement>(null)

  useEffect(() => {
    if (searchOpen) {
      searchInputRef.current?.focus()
    }
  }, [searchOpen])

  useEffect(() => {
    if (!searchOpen) return
    function handleClick(e: MouseEvent) {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target as Node)) {
        setSearchOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [searchOpen])

  return (
    <div className="min-h-screen ambient-glow flex">
      {/* Sidebar */}
      <aside
        ref={sidebarRef}
        className={[
          'hidden md:flex fixed top-0 left-0 bottom-0 border-r border-border flex-col items-center py-4 z-50 transition-all duration-200',
          searchOpen ? 'w-[240px] bg-[#0B1120]' : 'w-[60px] bg-white/[2%]',
        ].join(' ')}
      >
        {/* Logo */}
        <div className="w-[34px] h-[34px] rounded-[10px] bg-linear-135/srgb from-primary to-secondary flex items-center justify-center text-white text-xs font-extrabold shadow-glow mb-6">
          IC
        </div>

        {/* Nav items */}
        <nav className="flex flex-col gap-1.5 flex-1 w-full px-[10.5px]">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              title={label}
              className={({ isActive }) =>
                [
                  'relative h-9 rounded-lg flex items-center transition-colors',
                  searchOpen ? 'px-2.5 gap-3' : 'w-9 justify-center',
                  isActive
                    ? 'text-primary-light bg-primary-glow'
                    : 'text-text-faint hover:text-text-muted hover:bg-surface',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-[-10.5px] top-1/2 -translate-y-1/2 w-[3px] h-[18px] rounded-r-sm bg-linear-to-b from-primary to-secondary" />
                  )}
                  <span className="flex-shrink-0">{icon}</span>
                  {searchOpen && (
                    <span className="text-xs font-medium whitespace-nowrap">{label}</span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Search */}
        <div className="w-full px-3 mb-3">
          {searchOpen ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border">
              <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" className="text-text-faint flex-shrink-0">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search..."
                className="bg-transparent text-xs text-text-primary placeholder:text-text-faint outline-none w-full"
              />
              <button
                onClick={() => setSearchOpen(false)}
                className="text-text-faint hover:text-text-muted flex-shrink-0"
              >
                <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              title="Search"
              className="w-9 h-9 rounded-lg flex items-center justify-center text-text-faint hover:text-text-muted hover:bg-surface transition-colors mx-auto"
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            </button>
          )}
        </div>

        {/* Avatar */}
        <div className="flex flex-col items-center gap-2">
          <div className="w-[30px] h-[30px] rounded-full bg-surface-raised border border-border flex items-center justify-center text-[11px] font-semibold text-text-muted">
            K
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className={`flex-1 min-h-screen transition-all duration-200 ${searchOpen ? 'md:ml-[240px]' : 'md:ml-[60px]'}`}>
        <main className="px-8 py-7 max-w-[1100px]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
