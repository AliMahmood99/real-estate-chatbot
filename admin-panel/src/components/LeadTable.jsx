import React from 'react'
import { useNavigate } from 'react-router-dom'
import PlatformBadge from './PlatformBadge'

const STATUS_STYLES = {
  hot: { bg: 'bg-red-100', text: 'text-red-800' },
  warm: { bg: 'bg-orange-100', text: 'text-orange-800' },
  cold: { bg: 'bg-blue-100', text: 'text-blue-800' },
  new: { bg: 'bg-gray-100', text: 'text-gray-800' },
  converted: { bg: 'bg-green-100', text: 'text-green-800' },
  lost: { bg: 'bg-gray-300', text: 'text-gray-700' },
}

export default function LeadTable({ leads }) {
  const navigate = useNavigate()

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status) => {
    const style = STATUS_STYLES[status] || STATUS_STYLES.new
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text} capitalize`}>
        {status}
      </span>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Phone
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Platform
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Project
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Date
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {leads.map((lead) => (
            <tr
              key={lead.id}
              onClick={() => navigate(`/leads/${lead.id}`)}
              className="hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">
                  {lead.name || 'Unknown'}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-600">
                  {lead.phone || '-'}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <PlatformBadge platform={lead.platform} />
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {getStatusBadge(lead.status)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-600">
                  {lead.interested_projects?.[0] || '-'}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatDate(lead.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {leads.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No leads found
        </div>
      )}
    </div>
  )
}
