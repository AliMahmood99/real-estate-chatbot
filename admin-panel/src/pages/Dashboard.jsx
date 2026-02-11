import React, { useEffect, useState } from 'react'
import { Users, Flame, CalendarDays, TrendingUp, RefreshCw, MessageSquare } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api'
import StatsCard from '../components/StatsCard'
import LeadTable from '../components/LeadTable'

// Skeleton loader component
function Skeleton({ className }) {
  return <div className={`skeleton ${className}`} />
}

function DashboardSkeleton() {
  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto animate-pulse">
      <div className="mb-8">
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-28 rounded-2xl" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-80 rounded-2xl lg:col-span-1" />
        <Skeleton className="h-80 rounded-2xl lg:col-span-2" />
      </div>
    </div>
  )
}

// Custom tooltip for pie chart
function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-slate-100 px-4 py-3">
        <p className="text-sm font-semibold text-slate-800">{payload[0].name}</p>
        <p className="text-lg font-bold text-slate-900">{payload[0].value} leads</p>
      </div>
    )
  }
  return null
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      const data = await api.getDashboard()
      setStats(data)
      setError(null)
    } catch (err) {
      console.error('Failed to load dashboard:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  if (loading) return <DashboardSkeleton />

  if (error) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button
            onClick={() => loadDashboard()}
            className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!stats) return null

  // Platform data for pie chart
  const platformData = Object.entries(stats.leads_by_platform || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }))

  const PLATFORM_COLORS = {
    Whatsapp: '#22c55e',
    Messenger: '#3b82f6',
    Instagram: '#d946ef',
  }

  const hotLeads = stats.leads_by_status?.hot || 0
  const warmLeads = stats.leads_by_status?.warm || 0
  const totalLeads = stats.total_leads || 0

  // Status breakdown for mini visualization
  const statusBreakdown = Object.entries(stats.leads_by_status || {}).filter(([, v]) => v > 0)

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="animate-fade-in">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Rekaz CRM overview and analytics</p>
        </div>
        <button
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all disabled:opacity-50"
        >
          <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div className="animate-fade-in stagger-1">
          <StatsCard
            title="Total Leads"
            value={totalLeads}
            icon={Users}
            color="blue"
          />
        </div>
        <div className="animate-fade-in stagger-2">
          <StatsCard
            title="Hot Leads"
            value={hotLeads}
            icon={Flame}
            color="red"
          />
        </div>
        <div className="animate-fade-in stagger-3">
          <StatsCard
            title="Today's Leads"
            value={stats.leads_today}
            icon={CalendarDays}
            color="green"
          />
        </div>
        <div className="animate-fade-in stagger-4">
          <StatsCard
            title="This Week"
            value={stats.leads_this_week}
            icon={TrendingUp}
            color="purple"
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Platform Distribution */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6 animate-fade-in">
          <h2 className="text-sm font-semibold text-slate-800 mb-1">Leads by Platform</h2>
          <p className="text-xs text-slate-400 mb-4">Distribution across channels</p>

          {platformData.length > 0 ? (
            <div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={platformData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    stroke="none"
                  >
                    {platformData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PLATFORM_COLORS[entry.name] || '#94A3B8'} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="space-y-2 mt-4">
                {platformData.map((entry) => (
                  <div key={entry.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: PLATFORM_COLORS[entry.name] || '#94A3B8' }}
                      />
                      <span className="text-xs text-slate-600">{entry.name}</span>
                    </div>
                    <span className="text-xs font-semibold text-slate-800">{entry.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-52 flex flex-col items-center justify-center text-slate-400">
              <MessageSquare size={28} className="mb-2 opacity-40" />
              <p className="text-xs">No data yet</p>
            </div>
          )}
        </div>

        {/* Status Breakdown */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6 lg:col-span-2 animate-fade-in">
          <h2 className="text-sm font-semibold text-slate-800 mb-1">Lead Status Overview</h2>
          <p className="text-xs text-slate-400 mb-6">Current status distribution</p>

          {statusBreakdown.length > 0 ? (
            <div className="space-y-4">
              {/* Status bar */}
              <div className="flex h-3 rounded-full overflow-hidden bg-slate-100">
                {statusBreakdown.map(([status, count]) => {
                  const percentage = totalLeads > 0 ? (count / totalLeads) * 100 : 0
                  const colorMap = {
                    hot: '#ef4444',
                    warm: '#f59e0b',
                    cold: '#0ea5e9',
                    new: '#94a3b8',
                    converted: '#22c55e',
                    lost: '#6b7280',
                  }
                  return (
                    <div
                      key={status}
                      className="h-full transition-all duration-500"
                      style={{
                        width: `${Math.max(percentage, 2)}%`,
                        backgroundColor: colorMap[status] || '#94a3b8',
                      }}
                      title={`${status}: ${count}`}
                    />
                  )
                })}
              </div>

              {/* Status grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-6">
                {statusBreakdown.map(([status, count]) => {
                  const colorMap = {
                    hot: { bg: 'bg-red-50', text: 'text-red-600', dot: 'bg-red-500' },
                    warm: { bg: 'bg-amber-50', text: 'text-amber-600', dot: 'bg-amber-500' },
                    cold: { bg: 'bg-sky-50', text: 'text-sky-600', dot: 'bg-sky-500' },
                    new: { bg: 'bg-slate-50', text: 'text-slate-600', dot: 'bg-slate-400' },
                    converted: { bg: 'bg-emerald-50', text: 'text-emerald-600', dot: 'bg-emerald-500' },
                    lost: { bg: 'bg-gray-50', text: 'text-gray-500', dot: 'bg-gray-400' },
                  }
                  const c = colorMap[status] || colorMap.new
                  const percentage = totalLeads > 0 ? Math.round((count / totalLeads) * 100) : 0

                  return (
                    <div key={status} className={`${c.bg} rounded-xl p-3.5`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`w-2 h-2 rounded-full ${c.dot}`} />
                        <span className={`text-xs font-medium capitalize ${c.text}`}>{status}</span>
                      </div>
                      <p className="text-xl font-bold text-slate-800">{count}</p>
                      <p className="text-[10px] text-slate-400">{percentage}% of total</p>
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="h-52 flex flex-col items-center justify-center text-slate-400">
              <TrendingUp size={28} className="mb-2 opacity-40" />
              <p className="text-xs">No status data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Leads */}
      <div className="bg-white rounded-2xl border border-slate-100 animate-fade-in">
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Recent Leads</h2>
            <p className="text-xs text-slate-400 mt-0.5">Latest incoming leads</p>
          </div>
          <span className="text-[11px] font-medium text-slate-400 bg-slate-50 px-2.5 py-1 rounded-lg">
            {(stats.recent_leads || []).length} shown
          </span>
        </div>
        <LeadTable leads={stats.recent_leads || []} compact />
      </div>
    </div>
  )
}
