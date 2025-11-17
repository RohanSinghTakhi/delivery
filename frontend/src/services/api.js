import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken });
          const { access_token } = response.data;
          
          localStorage.setItem('access_token', access_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth APIs
export const auth = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me')
};

// Vendor APIs
export const vendors = {
  register: (data) => api.post('/vendors/register', data),
  getAll: () => api.get('/vendors'),
  getById: (id) => api.get(`/vendors/${id}`),
  getDrivers: (vendorId) => api.get(`/vendors/${vendorId}/drivers`)
};

// Driver APIs
export const drivers = {
  register: (data) => api.post('/drivers/register', data),
  getAll: (params) => api.get('/drivers', { params }),
  getById: (id) => api.get(`/drivers/${id}`),
  updateStatus: (id, status) => api.patch(`/drivers/${id}/status`, null, { params: { new_status: status } }),
  updateLocation: (id, latitude, longitude) => api.post(`/drivers/${id}/location`, null, { params: { latitude, longitude } })
};

// Order APIs
export const orders = {
  create: (data) => api.post('/orders', data),
  getAll: (params) => api.get('/orders', { params }),
  getById: (id) => api.get(`/orders/${id}`),
  updateStatus: (id, status) => api.patch(`/orders/${id}/status`, null, { params: { new_status: status } }),
  assignDriver: (orderId, driverId) => api.post(`/orders/${orderId}/assign`, null, { params: { driver_id: driverId } })
};

// Tracking APIs
export const tracking = {
  getByToken: (token) => axios.get(`${API_URL}/tracking/${token}`)
};

// Reports APIs
export const reports = {
  getVendorReport: (vendorId, date) => api.get(`/reports/vendors/${vendorId}`, { params: { date } }),
  getDriverReport: (driverId, startDate, endDate) => api.get(`/reports/drivers/${driverId}`, { params: { start_date: startDate, end_date: endDate } })
};

// Upload APIs
export const uploads = {
  uploadProof: (file, orderId) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/uploads/proof`, formData, {
      params: { order_id: orderId },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  uploadSignature: (file, orderId) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/uploads/signature`, formData, {
      params: { order_id: orderId },
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

export default api;