const API_BASE = '/api/admin'

export function getApiKey() {
  return localStorage.getItem('admin_api_key') || ''
}

export function setApiKey(key) {
  localStorage.setItem('admin_api_key', key)
}

async function request(endpoint, options = {}) {
  const apiKey = getApiKey()
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      ...options.headers,
    },
  })
  if (res.status === 401 || res.status === 403) {
    // Invalid API key — clear and reload
    localStorage.removeItem('admin_api_key')
    window.location.reload()
    throw new Error('Invalid API key')
  }
  if (!res.ok) throw new Error(`API Error: ${res.status}`)
  return res.json()
}

export const api = {
  getDashboard: () => request('/dashboard'),
  getLeads: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/leads?${query}`)
  },
  getLead: (id) => request(`/leads/${id}`),
  updateLead: (id, data) => request(`/leads/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),
  getLeadConversations: (id) => request(`/leads/${id}/conversations`),
  getConversationMessages: (id) => request(`/conversations/${id}/messages`),
  getProperties: () => request('/properties'),
}
