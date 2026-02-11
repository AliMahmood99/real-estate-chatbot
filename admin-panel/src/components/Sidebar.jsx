import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, Users, Building2, LogOut, X, ChevronRight } from 'lucide-react'

export default function Sidebar({ onClose }) {
  const location = useLocation()

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, description: 'Overview & stats' },
    { to: '/leads', label: 'Leads', icon: Users, description: 'Manage leads' },
  ]

  const handleLogout = () => {
    localStorage.removeItem('admin_api_key')
    window.location.reload()
  }

  return (
    <div className="w-[260px] bg-sidebar text-white flex flex-col h-screen">
      {/* Brand Header */}
      <div className="px-5 py-5 border-b border-white/[0.08]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Building2 size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">Rekaz CRM</h1>
              <p className="text-[11px] text-slate-400 -mt-0.5">Admin Panel</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X size={18} className="text-slate-400" />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-3">
          Menu
        </p>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = item.to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(item.to)

          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onClose}
              className={`
                group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200
                ${isActive
                  ? 'bg-blue-600/90 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-white/[0.06] hover:text-white'
                }
              `}
            >
              <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center transition-colors
                ${isActive ? 'bg-white/20' : 'bg-white/[0.04] group-hover:bg-white/[0.08]'}
              `}>
                <Icon size={17} />
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium block">{item.label}</span>
                <span className={`text-[10px] block -mt-0.5 ${isActive ? 'text-blue-100' : 'text-slate-500'}`}>
                  {item.description}
                </span>
              </div>
              {isActive && (
                <ChevronRight size={14} className="text-blue-200 shrink-0" />
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-4 pt-2 border-t border-white/[0.06]">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all duration-200"
        >
          <div className="w-8 h-8 rounded-lg bg-white/[0.04] flex items-center justify-center">
            <LogOut size={17} />
          </div>
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </div>
  )
}
