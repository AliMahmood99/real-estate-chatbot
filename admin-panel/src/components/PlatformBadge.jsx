import React from 'react'

const PLATFORM_STYLES = {
  whatsapp: { bg: 'bg-green-100', text: 'text-green-800', label: 'WhatsApp' },
  messenger: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Messenger' },
  instagram: { bg: 'bg-purple-100', text: 'text-purple-800', label: 'Instagram' },
}

export default function PlatformBadge({ platform }) {
  const style = PLATFORM_STYLES[platform] || { bg: 'bg-gray-100', text: 'text-gray-800', label: platform }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  )
}
