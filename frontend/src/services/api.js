import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
});

export const searchHCPs      = (q = '')      => api.get(`/api/hcps?q=${encodeURIComponent(q)}`);
export const getHCP          = (id)          => api.get(`/api/hcps/${id}`);
export const searchMaterials = (q = '')      => api.get(`/api/materials?q=${encodeURIComponent(q)}`);
export const createInteraction = (data)      => api.post('/api/interactions', data);
export const listInteractions  = ()          => api.get('/api/interactions');
export const getInteraction  = (id)          => api.get(`/api/interactions/${id}`);
export const updateInteraction = (id, data)  => api.put(`/api/interactions/${id}`, data);
export const chatWithAgent   = (payload)     => api.post('/api/agent/chat', payload);
export const clearAgentSession = (sessionId) => api.delete(`/api/agent/chat/${sessionId}`);
