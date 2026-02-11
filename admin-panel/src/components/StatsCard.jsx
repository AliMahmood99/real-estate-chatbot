import React from 'react'

export default function StatsCard({ title, value, icon: Icon, trend, color = 'blue' }) {
  const colorMap = {
    blue: {
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-600',
      accent: 'from-blue-600 to-blue-700',
    },
    red: {
      iconBg: 'bg-red-50',
      iconColor: 'text-red-600',
      accent: 'from-red-600 to-red-700',
    },
    green: {
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      accent: 'from-emerald-600 to-emerald-700',
    },
    amber: {
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
      accent: 'from-amber-600 to-amber-700',
    },
    purple: {
      iconBg: 'bg-purple-50',
      iconColor: 'text-purple-600',
      accent: 'from-purple-600 to-purple-700',
    },
  }

  const colors = colorMap[color] || colorMap.blue

  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-5 card-hover relative overflow-hidden group">
      {/* Subtle accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r ${colors.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-[13px] font-medium text-slate-500 leading-tight">{title}</p>
          <div className="flex items-baseline gap-2 mt-2">
            <p className="text-3xl font-bold text-slate-900 tracking-tight">
              {value ?? 0}
            </p>
            {trend !== undefined && trend !== null && (
              <span className={`text-xs font-semibold ${trend >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
            )}
          </div>
        </div>

        <div className={`${colors.iconBg} p-2.5 rounded-xl`}>
          {Icon && <Icon size={20} className={colors.iconColor} />}
        </div>
      </div>
    </div>
  )
}
