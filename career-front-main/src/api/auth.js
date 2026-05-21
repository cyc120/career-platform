import api from './client'

export const authApi = {
  register(data) {
    return api.post('/auth/register', data)
  },
  login(data) {
    return api.post('/auth/login', new URLSearchParams(data), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
  },
  refresh(refreshToken) {
    return api.post('/auth/refresh', { refresh_token: refreshToken })
  },
  logout(refreshToken) {
    return api.post('/auth/logout', { refresh_token: refreshToken })
  },
  guestToken() {
    return api.post('/auth/guest-token')
  },
}
