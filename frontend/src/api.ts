import axios from 'axios';

export const api = axios.create({baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'});
const accessKey = 'bookleaf_access';
const refreshKey = 'bookleaf_refresh';
let refreshRequest: Promise<string> | null = null;
let lostSession: (() => void) | null = null;

export function setSessionLostHandler(fn: () => void) { lostSession = fn; }
export function saveTokens(tokens: {access: string; refresh: string}) {
  sessionStorage.setItem(accessKey, tokens.access);
  sessionStorage.setItem(refreshKey, tokens.refresh);
}
export function clearTokens() {
  sessionStorage.removeItem(accessKey);
  sessionStorage.removeItem(refreshKey);
}
export function hasSession() { return !!sessionStorage.getItem(refreshKey); }
export function refreshToken() { return sessionStorage.getItem(refreshKey); }

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem(accessKey);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(undefined, async (error) => {
  const original = error.config;
  if (error.response?.status !== 401 || !original || original._retried ||
      original.url?.includes('/auth/login/') || original.url?.includes('/auth/refresh/')) {
    return Promise.reject(error);
  }
  const refresh = sessionStorage.getItem(refreshKey);
  if (!refresh) return Promise.reject(error);
  original._retried = true;
  try {
    refreshRequest ??= axios.post(`${api.defaults.baseURL}/auth/refresh/`, {refresh})
      .then(({data}) => { saveTokens({access:data.access, refresh:data.refresh || refresh}); return data.access; })
      .finally(() => { refreshRequest = null; });
    original.headers.Authorization = `Bearer ${await refreshRequest}`;
    return api(original);
  } catch (refreshError) {
    clearTokens(); lostSession?.();
    return Promise.reject(refreshError);
  }
});

export function apiError(error: unknown): string {
  if (!axios.isAxiosError(error)) return 'Something went wrong. Please try again.';
  const payload = error.response?.data?.error?.detail ?? error.response?.data;
  if (typeof payload === 'string') return payload;
  if (typeof payload?.detail === 'string') return payload.detail;
  if (payload && typeof payload === 'object') {
    const first = Object.values(payload)[0];
    if (Array.isArray(first)) return String(first[0]);
    if (typeof first === 'string') return first;
  }
  return error.response?.status === 503 ? 'The server is waking up. Please try again shortly.' : 'Something went wrong. Please try again.';
}
