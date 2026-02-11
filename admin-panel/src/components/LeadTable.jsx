import React from 'react'
import { useNavigate } from 'react-router-dom'
import PlatformBadge from './PlatformBadge'
import { ChevronRight, User, Phone } from 'lucide-react'

const STATUS_CONFIG = {
  hot: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200/60', dot: 'bg-red-500', label: 'Hot' },
  warm: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200/60', dot: 'bg-amber-500', label: 'Warm' },
  cold: { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200/60', dot: 'bg-sky-500', label: 'Cold' },
  new: { bg: 'bg-slate-50', text: 'text-slate-600', border: 'border-slate-200/60', dot: 'bg-slate-400', label: 'New' },
  converted: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200/60', dot: 'bg-emerald-500', label: 'Converted' },
  lost: { bg: 'bg-gray-100', text: 'text-gray-500', border: 'border-gray-200/60', dot: 'bg-gray-400', label: 'Lost' },
}

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.new
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${config.bg} ${config.text} ${config.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  )
}

export default function LeadTable({ leads, compact = false }) {
  const navigate = useNavigate()

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    })
  }

  if (leads.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <User size={24} className="text-slate-400" />
        </div>
        <p className="text-sm font-medium text-slate-500">No leads found</p>
        <p className="text-xs text-slate-400 mt-1">Leads will appear here when customers message your bot</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="text-left py-3 px-4 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Lead</th>
            <th className="text-left py-3 px-4 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Platform</th>
            <th className="text-left py-3 px-4 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Status</th>
            {!compact && (
              <th className="text-left py-3 px-4 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Project</th>
            )}
            <th className="text-left py-3 px-4 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Last Message</th>
            <th className="py-3 px-4 w-8"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {leads.map((lead, idx) => (
            <tr
              key={lead.id}
              onClick={() => navigate(`/leads/${lead.id}`)}
              className="group hover:bg-blue-50/40 cursor-pointer transition-colors duration-150"
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              <td className="py-3.5 px-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center shrink-0">
                    <span className="text-[11px] font-bold text-slate-500">
                      {(lead.name || '?')[0].toUpperCase()}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">
                      {lead.name || 'Unknown'}
                    </p>
                    {lead.phone && (
                      <p className="text-[11px] text-slate-400 flex items-center gap-1">
                        <Phone size={10} />
                        {lead.phone}
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="py-3.5 px-4">
                <PlatformBadge platform={lead.platform} />
              </td>
              <td className="py-3.5 px-4">
                <StatusBadge status={lead.status} />
              </td>
              {!compact && (
                <td className="py-3.5 px-4">
                  <span className="text-sm text-slate-500 truncate block max-w-[160px]">
                    {lead.interested_projects?.[0] || '-'}
                  </span>
                </td>
              )}
              <td className="py-3.5 px-4">
                <span className="text-xs text-slate-400">{formatDate(lead.last_message_at)}</span>
              </td>
              <td className="py-3.5 px-2">
                <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-500 transition-colors" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export { StatusBadge }
