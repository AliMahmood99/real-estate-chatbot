import React from 'react'
import PlatformBadge from './PlatformBadge'

export default function ChatBubble({ message }) {
  const isCustomer = message.sender_type === 'customer'

  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={`flex ${isCustomer ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`max-w-2xl ${isCustomer ? 'mr-auto' : 'ml-auto'}`}>
        <div
          className={`rounded-lg px-4 py-3 ${
            isCustomer
              ? 'bg-gray-100 text-gray-900'
              : 'bg-blue-600 text-white'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className={`flex items-center gap-2 mt-1 text-xs text-gray-500 ${isCustomer ? '' : 'justify-end'}`}>
          <span>{formatTime(message.timestamp)}</span>
          {isCustomer && <PlatformBadge platform={message.platform} />}
          {!isCustomer && <span className="text-blue-600 font-medium">Bot</span>}
        </div>
      </div>
    </div>
  )
}
