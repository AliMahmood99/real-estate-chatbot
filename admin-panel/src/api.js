const API_BASE = '/api/admin'
const API_KEY = localStorage.getItem('admin_api_key') || 'your_secure_admin_api_key'

async function request(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      ...options.headers,
    },
  })
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
