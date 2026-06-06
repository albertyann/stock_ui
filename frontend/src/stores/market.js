import { defineStore } from 'pinia'

const MARKET_KEY = 'trading_market'
const MARKET_A = 'A'
const MARKET_HK = 'HK'
const VALID_MARKETS = new Set([MARKET_A, MARKET_HK])

export const useMarketStore = defineStore('market', {
  state: () => ({
    currentMarket: MARKET_A
  }),

  getters: {
    isHK: (state) => state.currentMarket === MARKET_HK,
    isA: (state) => state.currentMarket === MARKET_A
  },

  actions: {
    initMarket() {
      try {
        const saved = localStorage.getItem(MARKET_KEY)
        if (saved && VALID_MARKETS.has(saved)) {
          this.currentMarket = saved
        }
      } catch (e) {
        console.warn('Failed to read market from localStorage:', e)
      }
    },

    setMarket(market) {
      if (!VALID_MARKETS.has(market)) {
        console.warn(`Invalid market value: ${market}`)
        return
      }
      this.currentMarket = market
      try {
        localStorage.setItem(MARKET_KEY, market)
      } catch (e) {
        console.warn('Failed to save market to localStorage:', e)
      }
    },

    toggleMarket() {
      this.setMarket(this.currentMarket === MARKET_A ? MARKET_HK : MARKET_A)
    }
  }
})
