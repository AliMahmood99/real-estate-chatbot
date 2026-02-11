import React from 'react'

export default function StatsCard({ title, value, icon: Icon, change }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}% from last period
            </p>
          )}
        </div>
        {Icon && (
          <div className="bg-blue-100 p-3 rounded-lg">
            <Icon size={24} className="text-blue-600" />
          </div>
        )}
      </div>
    </div>
  )
}
