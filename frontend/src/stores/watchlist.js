import { defineStore } from 'pinia'
import { watchlistApi } from '@/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    watchlists: [],
    currentWatchlist: null,
    stocks: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchWatchlists() {
      this.loading = true
      try {
        const response = await watchlistApi.getAll()
        this.watchlists = response.data
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async fetchStocks(watchlistId) {
      this.loading = true
      try {
        const response = await watchlistApi.getStocks(watchlistId)
        this.currentWatchlist = response.data
        this.stocks = response.data.stocks
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },

    async createWatchlist(data) {
      try {
        const response = await watchlistApi.create(data)
        this.watchlists.push(response.data)
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async addStock(watchlistId, tsCode) {
      try {
        await watchlistApi.addStock(watchlistId, { ts_code: tsCode })
        await this.fetchStocks(watchlistId)
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async removeStock(watchlistId, stockId) {
      try {
        await watchlistApi.removeStock(watchlistId, stockId)
        await this.fetchStocks(watchlistId)
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async updateWatchlist(id, data) {
      try {
        const response = await watchlistApi.update(id, data)
        const index = this.watchlists.findIndex(w => w.id === id)
        if (index !== -1) {
          this.watchlists[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    async deleteWatchlist(id) {
      try {
        await watchlistApi.delete(id)
        // 从列表中移除
        this.watchlists = this.watchlists.filter(w => w.id !== id)
      } catch (error) {
        this.error = error.message
        throw error
      }
    }
  }
})
