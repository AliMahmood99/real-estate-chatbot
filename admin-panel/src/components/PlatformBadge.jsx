import React from 'react'

const PLATFORM_CONFIG = {
  whatsapp: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200/60',
    dot: 'bg-emerald-500',
    label: 'WhatsApp',
  },
  messenger: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    border: 'border-blue-200/60',
    dot: 'bg-blue-500',
    label: 'Messenger',
  },
  instagram: {
    bg: 'bg-fuchsia-50',
    text: 'text-fuchsia-700',
    border: 'border-fuchsia-200/60',
    dot: 'bg-fuchsia-500',
    label: 'Instagram',
  },
}

export default function PlatformBadge({ platform, size = 'sm' }) {
  const config = PLATFORM_CONFIG[platform] || {
    bg: 'bg-slate-50',
    text: 'text-slate-600',
    border: 'border-slate-200/60',
    dot: 'bg-slate-400',
    label: platform || 'Unknown',
  }

  const sizeClasses = size === 'sm'
    ? 'px-2 py-0.5 text-[11px]'
    : 'px-2.5 py-1 text-xs'

  return (
    <span className={`
      inline-flex items-center gap-1.5 rounded-full font-medium border
      ${config.bg} ${config.text} ${config.border} ${sizeClasses}
    `}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  )
}
