import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  const isLoggedIn = computed(() => !!accessToken.value)

  function _saveTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  async function login(username, password) {
    const { data } = await authApi.login({ username, password })
    _saveTokens(data.access_token, data.refresh_token)
    user.value = data.user
    return data
  }

  async function register(username, email, password) {
    const { data } = await authApi.register({ username, email, password })
    _saveTokens(data.access_token, data.refresh_token)
    user.value = data.user
    return data
  }

  async function logout() {
    try {
      await authApi.logout(refreshToken.value)
    } catch {
      // ignore
    }
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.clear()
  }

  async function refresh() {
    if (!refreshToken.value) return
    try {
      const { data } = await authApi.refresh(refreshToken.value)
      _saveTokens(data.access_token, data.refresh_token)
    } catch {
      accessToken.value = null
      refreshToken.value = null
      user.value = null
      localStorage.clear()
    }
  }

  return { user, accessToken, refreshToken, isLoggedIn, login, register, logout, refresh }
})
