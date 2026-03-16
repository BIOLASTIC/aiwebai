import axios from 'axios';

const API_BASE = `http://${window.location.hostname}:6400`;
const token = localStorage.getItem('token');

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});

export const modelApi = {
  getModelsByAccountAndFeature: async (accountId: string, feature: string) => {
    return api.get(`/admin/accounts/${accountId}/models`, { 
      params: { feature } 
    });
  }
};

export default api;