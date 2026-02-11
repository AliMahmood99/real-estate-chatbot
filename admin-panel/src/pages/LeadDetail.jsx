import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Save, User, Phone, Mail, DollarSign, Clock, Building,
  MessageSquare, Calendar, CheckCircle, AlertCircle
} from 'lucide-react'
import { api } from '../api'
import PlatformBadge from '../components/PlatformBadge'
import ChatBubble from '../components/ChatBubble'
import { StatusBadge } from '../components/LeadTable'

const STATUS_OPTIONS = [
  { value: 'new', label: 'New', color: 'bg-slate-400' },
  { value: 'hot', label: 'Hot', color: 'bg-red-500' },
  { value: 'warm', label: 'Warm', color: 'bg-amber-500' },
  { value: 'cold', label: 'Cold', color: 'bg-sky-500' },
  { value: 'converted', label: 'Converted', color: 'bg-emerald-500' },
  { value: 'lost', label: 'Lost', color: 'bg-gray-400' },
]

function InfoRow({ icon: Icon, label, value, iconColor = 'text-slate-400' }) {
  return (
    <div className="flex items-start gap-3 py-3">
      <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center shrink-0 mt-0.5">
        <Icon size={15} className={iconColor} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">{label}</p>
        <p className="text-sm text-slate-800 mt-0.5 break-words">{value || '-'}</p>
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto animate-pulse">
      <div className="skeleton h-5 w-24 mb-6 rounded-lg" />
      <div className="skeleton h-8 w-48 mb-2 rounded-lg" />
      <div className="skeleton h-4 w-64 mb-8 rounded-lg" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="skeleton h-[500px] rounded-2xl" />
        <div className="skeleton h-[500px] rounded-2xl lg:col-span-2" />
      </div>
    </div>
  )
}

export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [conversations, setConversations] = useState([])
  const [messages, setMessages] = useState({})
  const [editData, setEditData] = useState({ status: '', notes: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
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

      const convData = await api.getLeadConversations(id)
      setConversations(convData)

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
      setSaveSuccess(false)
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
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 3000)
      }
    } catch (err) {
      console.error('Failed to update lead:', err)
      setError('Failed to update lead')
    } finally {
      setSaving(false)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalMessages = conversations.reduce((sum, c) => sum + (c.message_count || 0), 0)

  if (loading) return <LoadingSkeleton />

  if (error || !lead) {
    return (
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        <button
          onClick={() => navigate('/leads')}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-6 transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Leads
        </button>
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
          <AlertCircle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-red-700 font-medium">{error || 'Lead not found'}</p>
          <button
            onClick={() => loadLeadDetails()}
            className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 animate-fade-in">
        <button
          onClick={() => navigate('/leads')}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 mb-4 transition-colors"
        >
          <ArrowLeft size={16} />
          <span>Back to Leads</span>
        </button>

        <div className="flex items-start gap-4">
          {/* Avatar */}
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-md shadow-blue-500/20 shrink-0">
            <span className="text-lg font-bold text-white">
              {(lead.name || '?')[0].toUpperCase()}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                {lead.name || 'Unknown Lead'}
              </h1>
              <PlatformBadge platform={lead.platform} size="md" />
            </div>
            <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {formatDate(lead.created_at)}
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare size={12} />
                {totalMessages} messages
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Save success toast */}
      {saveSuccess && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-xl animate-fade-in">
          <CheckCircle size={16} className="text-emerald-600" />
          <span className="text-sm font-medium text-emerald-700">Changes saved successfully</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Lead Info */}
        <div className="lg:col-span-1 space-y-5">
          {/* Info Card */}
          <div className="bg-white rounded-2xl border border-slate-100 p-5 animate-slide-in-left sticky top-6">
            <h2 className="text-sm font-semibold text-slate-800 mb-4">Lead Information</h2>

            {/* Status selector */}
            <div className="mb-5">
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2">Status</p>
              <div className="grid grid-cols-3 gap-1.5">
                {STATUS_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => setEditData(prev => ({ ...prev, status: opt.value }))}
                    className={`
                      flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-[11px] font-medium transition-all
                      ${editData.status === opt.value
                        ? 'bg-blue-50 text-blue-700 border-2 border-blue-300 shadow-sm'
                        : 'bg-slate-50 text-slate-500 border-2 border-transparent hover:bg-slate-100'
                      }
                    `}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${opt.color}`} />
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Info rows */}
            <div className="divide-y divide-slate-50">
              <InfoRow icon={User} label="Name" value={lead.name} />
              <InfoRow icon={Phone} label="Phone" value={lead.phone} iconColor="text-emerald-500" />
              <InfoRow icon={Mail} label="Email" value={lead.email} />
              <InfoRow icon={DollarSign} label="Budget" value={lead.budget_range} iconColor="text-amber-500" />
              <InfoRow icon={Clock} label="Timeline" value={lead.timeline} />
              <InfoRow icon={Building} label="Preferred Type" value={lead.preferred_type} />
              <InfoRow icon={Building} label="Preferred Size" value={lead.preferred_size} />
              <InfoRow icon={DollarSign} label="Payment Plan" value={lead.payment_plan} />
            </div>

            {/* Interested projects */}
            {lead.interested_projects && lead.interested_projects.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2">Interested Projects</p>
                <div className="flex flex-wrap gap-1.5">
                  {lead.interested_projects.map((project, idx) => (
                    <span key={idx} className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-lg border border-blue-100">
                      {project}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Notes */}
            <div className="mt-5 pt-4 border-t border-slate-100">
              <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-2">Notes</p>
              <textarea
                value={editData.notes}
                onChange={(e) => setEditData(prev => ({ ...prev, notes: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 outline-none transition-all resize-none placeholder-slate-400"
                placeholder="Add notes about this lead..."
              />
            </div>

            {/* Save button */}
            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full mt-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white py-2.5 px-4 rounded-xl font-medium text-sm hover:from-blue-500 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-md shadow-blue-600/15"
            >
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save size={15} />
                  <span>Save Changes</span>
                </>
              )}
            </button>

            {/* Timestamps */}
            <div className="mt-4 pt-3 border-t border-slate-50 space-y-1">
              <p className="text-[10px] text-slate-400">Created: {formatDate(lead.created_at)}</p>
              <p className="text-[10px] text-slate-400">Updated: {formatDate(lead.updated_at)}</p>
            </div>
          </div>
        </div>

        {/* Right: Conversations */}
        <div className="lg:col-span-2 animate-slide-in-right">
          <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
            {/* Chat header */}
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">Conversations</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {conversations.length} conversation{conversations.length !== 1 ? 's' : ''} / {totalMessages} messages
                </p>
              </div>
            </div>

            {/* Messages area */}
            <div className="max-h-[calc(100vh-280px)] overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="py-20 text-center">
                  <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <MessageSquare size={24} className="text-slate-300" />
                  </div>
                  <p className="text-sm font-medium text-slate-400">No conversations yet</p>
                  <p className="text-xs text-slate-300 mt-1">Messages will appear here</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-50">
                  {conversations.map((conv) => (
                    <div key={conv.id} className="p-6">
                      {/* Conversation header */}
                      <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-2.5">
                          <PlatformBadge platform={conv.platform} size="md" />
                          <span className="text-xs text-slate-400">
                            Started {formatDate(conv.started_at)}
                          </span>
                        </div>
                        <span className="text-[11px] font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded-lg">
                          {conv.message_count || 0} msgs
                        </span>
                      </div>

                      {/* Messages */}
                      <div className="space-y-1">
                        {messages[conv.id] && messages[conv.id].length > 0 ? (
                          messages[conv.id].map((msg) => (
                            <ChatBubble key={msg.id} message={msg} />
                          ))
                        ) : (
                          <p className="text-xs text-slate-400 text-center py-4">No messages in this conversation</p>
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
    </div>
  )
}
