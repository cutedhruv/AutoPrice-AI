const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json();
}

export const api = {
  API_BASE,
  WS_URL,
  getProducts: () => getJson('/api/products'),
  getDecisions: (limit = 30) => getJson(`/api/decisions?limit=${limit}`),
  getUpdates: (limit = 40) => getJson(`/api/updates?limit=${limit}`),
  getActivity: (limit = 50) => getJson(`/api/agent-activity?limit=${limit}`),
  getStats: () => getJson('/api/dashboard/stats'),
};

