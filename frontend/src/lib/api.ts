import axios from 'axios';

const API_BASE = `http://${window.location.hostname}:6400`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inject fresh token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const modelApi = {
  getModelsByAccountAndFeature: async (accountId: string, feature: string) => {
    return api.get(`/admin/accounts/${accountId}/models`, { 
      params: { feature } 
    });
  }
};

export default api;