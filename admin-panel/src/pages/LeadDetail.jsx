import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Save } from 'lucide-react'
import { api } from '../api'
import PlatformBadge from '../components/PlatformBadge'
import ChatBubble from '../components/ChatBubble'

const STATUS_OPTIONS = [
  { value: 'new', label: 'New' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
  { value: 'cold', label: 'Cold' },
  { value: 'converted', label: 'Converted' },
  { value: 'lost', label: 'Lost' },
]

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [conversations, setConversations] = useState([])
  const [messages, setMessages] = useState({})
  const [editData, setEditData] = useState({ status: '', notes: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadLeadDetails()
  }, [id])

  const loadLeadDetails = async () => {
    try {
      setLoading(true)
      const leadData = await api.getLead(id)
      setLead(leadData)
      setEditData({ status: leadData.status, notes: leadData.notes || '' })

      // Load conversations
      const convData = await api.getLeadConversations(id)
      setConversations(convData)

      // Load messages for each conversation
      const messagesData = {}
      for (const conv of convData) {
        const msgs = await api.getConversationMessages(conv.id)
        messagesData[conv.id] = msgs
      }
      setMessages(messagesData)

      setError(null)
    } catch (err) {
      console.error('Failed to load lead details:', err)
      setError('Failed to load lead details')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const updateData = {}
      if (editData.status !== lead.status) {
        updateData.status = editData.status
      }
      if (editData.notes !== lead.notes) {
        updateData.notes = editData.notes
      }

      if (Object.keys(updateData).length > 0) {
        await api.updateLead(id, updateData)
        await loadLeadDetails()
        alert('Lead updated successfully')
      }
    } catch (err) {
      console.error('Failed to update lead:', err)
      alert('Failed to update lead')
    } finally {
      setSaving(false)
    }
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading lead details...</div>
        </div>
      </div>
    )
  }

  if (error || !lead) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error || 'Lead not found'}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/leads')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={20} />
          Back to Leads
        </button>
        <h1 className="text-3xl font-bold text-gray-900">
          {lead.name || 'Unknown Lead'}
        </h1>
        <p className="text-gray-500 mt-1">Lead ID: {lead.id}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lead Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm p-6 sticky top-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Lead Information</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Platform</label>
                <PlatformBadge platform={lead.platform} />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Status</label>
                <select
                  value={editData.status}
                  onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {STATUS_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Name</label>
                <p className="text-gray-900">{lead.name || '-'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Phone</label>
                <p className="text-gray-900">{lead.phone || '-'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Email</label>
                <p className="text-gray-900">{lead.email || '-'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Budget</label>
                <p className="text-gray-900">{lead.budget_range || '-'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Timeline</label>
                <p className="text-gray-900">{lead.timeline || '-'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Interested Projects</label>
                <div className="space-y-1">
                  {lead.interested_projects && lead.interested_projects.length > 0 ? (
                    lead.interested_projects.map((project, idx) => (
                      <p key={idx} className="text-gray-900 text-sm">• {project}</p>
                    ))
                  ) : (
                    <p className="text-gray-900">-</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Notes</label>
                <textarea
                  value={editData.notes}
                  onChange={(e) => setEditData(prev => ({ ...prev, notes: e.target.value }))}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Add notes about this lead..."
                />
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Save size={16} />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">Created: {formatDate(lead.created_at)}</p>
                <p className="text-xs text-gray-500">Last Updated: {formatDate(lead.updated_at)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Conversations */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Conversations</h2>

            {conversations.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No conversations yet
              </div>
            ) : (
              <div className="space-y-8">
                {conversations.map((conv) => (
                  <div key={conv.id} className="border-b border-gray-200 pb-8 last:border-b-0">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <PlatformBadge platform={conv.platform} />
                        <span className="text-sm text-gray-500">
                          Started: {formatDate(conv.started_at)}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {conv.message_count} messages
                      </span>
                    </div>

                    {/* Messages */}
                    <div className="space-y-2">
                      {messages[conv.id] && messages[conv.id].length > 0 ? (
                        messages[conv.id].map((msg) => (
                          <ChatBubble key={msg.id} message={msg} />
                        ))
                      ) : (
                        <p className="text-gray-500 text-sm">No messages</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
