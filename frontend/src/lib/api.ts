import { client } from './api/generated/client.gen';

// Configuración global del cliente generado
client.setConfig({
  baseURL: (process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/api\/v1\/?$/, ''),
});

// Interceptor para añadir el token JWT
client.instance.interceptors.request.use((request) => {
  if (typeof window !== 'undefined') {
    const token = document.cookie
      .split('; ')
      .find((row) => row.startsWith('access_token='))
      ?.split('=')[1];

    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }
  }
  return request;
});

// También exportamos un cliente axios personalizado si fuera necesario para otros usos
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = document.cookie
      .split('; ')
      .find((row) => row.startsWith('access_token='))
      ?.split('=')[1];

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh en 401 utilizando refresh_token de cookies
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: any = error.config;
    const status = error?.response?.status;
    if (status === 401 && !originalRequest._retry && typeof window !== 'undefined') {
      originalRequest._retry = true;
      const cookies = document.cookie.split('; ').reduce<Record<string, string>>((acc, row) => {
        const [k, v] = row.split('=');
        if (k && v) acc[k] = v;
        return acc;
      }, {});
      const refreshToken = cookies['refresh_token'];
      if (!refreshToken) {
        return Promise.reject(error);
      }
      try {
        const base = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
        const res = await axios.post(`${base}/auth/refresh`, null, {
          params: { token_str: refreshToken },
          headers: { 'Content-Type': 'application/json' },
        });
        const { access_token, refresh_token } = res.data || {};
        if (access_token) {
          // Actualizar cookies
          const expiresAccess = new Date(Date.now() + 30 * 60 * 1000); // ~30 mins
          document.cookie = `access_token=${access_token}; expires=${expiresAccess.toUTCString()}; path=/`;
          if (refresh_token) {
            const expiresRefresh = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
            document.cookie = `refresh_token=${refresh_token}; expires=${expiresRefresh.toUTCString()}; path=/`;
          }
          // Reintentar la solicitud original con el nuevo token
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (e) {
        // Si falla el refresh, continuamos con el error original
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { client };
