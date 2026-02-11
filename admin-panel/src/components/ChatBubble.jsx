import React from 'react'
import { Bot, User } from 'lucide-react'

export default function ChatBubble({ message }) {
  const isCustomer = message.sender_type === 'customer'

  const formatTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className={`flex gap-2.5 ${isCustomer ? 'justify-start' : 'justify-end'} mb-3`}>
      {/* Customer avatar */}
      {isCustomer && (
        <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center shrink-0 mt-1">
          <User size={14} className="text-slate-500" />
        </div>
      )}

      <div className={`max-w-[75%] ${isCustomer ? 'mr-auto' : 'ml-auto'}`}>
        {/* Sender label */}
        <p className={`text-[10px] font-medium mb-1 ${isCustomer ? 'text-slate-400' : 'text-blue-400 text-right'}`}>
          {isCustomer ? 'Customer' : 'Bot'}
        </p>

        {/* Message bubble */}
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isCustomer
              ? 'bg-slate-100 text-slate-800 rounded-tl-md'
              : 'bg-blue-600 text-white rounded-tr-md'
          }`}
        >
          <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Timestamp */}
        <p className={`text-[10px] text-slate-400 mt-1 ${isCustomer ? '' : 'text-right'}`}>
          {formatTime(message.timestamp)}
        </p>
      </div>

      {/* Bot avatar */}
      {!isCustomer && (
        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1">
          <Bot size={14} className="text-blue-600" />
        </div>
      )}
    </div>
  )
}
