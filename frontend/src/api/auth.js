import api from '@/api/index.js'

export const authApi = {
  login: (phone, totp_code) => api.post('/auth/login', { phone, totp_code }),
  enroll: (phone, invitation_code) =>
    api.post('/auth/enroll', { phone, invitation_code }),
  enrollConfirm: (pending_token, totp_code) =>
    api.post('/auth/enroll/confirm', { pending_token, totp_code }),
  refresh: () => api.post('/auth/refresh'),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  listUsers: () => api.get('/auth/users'),
  createUser: (phone, role) => api.post('/auth/users', { phone, role }),
  updateUser: (id, params) => api.patch(`/auth/users/${id}`, params),
}

export default authApi
