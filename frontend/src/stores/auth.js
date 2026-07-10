import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    initialized: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => state.user?.role === 'admin',
    role: (state) => state.user?.role || null,
    phone: (state) => state.user?.phone || '',
  },

  actions: {
    async init() {
      try {
        const res = await authApi.me()
        this.user = res.data
      } catch (e) {
        this.user = null
      } finally {
        this.initialized = true
      }
    },

    async login(phone, totp_code) {
      const res = await authApi.login(phone, totp_code)
      this.user = res.data
      return res
    },

    async enroll(phone, invitation_code) {
      return await authApi.enroll(phone, invitation_code)
    },

    async enrollConfirm(pending_token, totp_code) {
      const res = await authApi.enrollConfirm(pending_token, totp_code)
      this.user = res.data
      return res
    },

    async logout() {
      try {
        await authApi.logout()
      } catch (e) {
        // 即使后端调用失败也要本地登出
      }
      this.user = null
    },

    setUser(user) {
      this.user = user
    },

    clearUser() {
      this.user = null
    },
  },
})
