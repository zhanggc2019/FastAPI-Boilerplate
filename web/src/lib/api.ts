import axios, { AxiosHeaders } from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

const bootstrapToken = localStorage.getItem('token');
if (bootstrapToken) {
  api.defaults.headers.common.Authorization = `Bearer ${bootstrapToken}`;
  console.info('[auth] bootstrap token loaded', bootstrapToken ? 'yes' : 'no');
} else {
  console.info('[auth] bootstrap token missing');
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  console.info('[auth] request token', token ? 'present' : 'missing', config.url);
  if (token) {
    const headers =
      config.headers instanceof AxiosHeaders
        ? config.headers
        : AxiosHeaders.from(config.headers ?? {});
    headers.set('Authorization', `Bearer ${token}`);
    config.headers = headers;
  }
  return config;
});

export default api;
