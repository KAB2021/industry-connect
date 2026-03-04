import { NavLink, Outlet } from 'react-router'

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/records', label: 'Records' },
  { to: '/upload', label: 'Upload' },
  { to: '/analysis', label: 'Analysis' },
]

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-8">
            <span className="text-lg font-semibold text-gray-900">
              IndustryConnect
            </span>
            <div className="flex gap-1">
              {navItems.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    [
                      'px-4 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                    ].join(' ')
                  }
                >
                  {label}
                </NavLink>
              ))}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
