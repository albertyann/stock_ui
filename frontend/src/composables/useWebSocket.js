import { ref, reactive, onMounted, onUnmounted } from 'vue'

const WS_URL = `ws://${window.location.host}/ws/stocks`

export function useWebSocket() {
  const ws = ref(null)
  const isConnected = ref(false)
  const lastMessage = ref(null)
  const subscribedStocks = reactive(new Set())
  const connectionError = ref(null)
  let reconnectTimer = null
  let pingTimer = null
  
  const connect = () => {
    try {
      const clientId = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      ws.value = new WebSocket(`${WS_URL}?client_id=${clientId}`)
      
      ws.value.onopen = () => {
        console.log('WebSocket connected')
        isConnected.value = true
        connectionError.value = null
        
        if (subscribedStocks.size > 0) {
          subscribe(Array.from(subscribedStocks))
        }
        
        startPing()
      }
      
      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          lastMessage.value = data
          
          if (data.type === 'pong') {
            console.log('Ping-pong latency:', Date.now() - data.timestamp, 'ms')
          }
        } catch (e) {
          console.error('Failed to parse message:', e)
        }
      }
      
      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        connectionError.value = 'Connection error'
      }
      
      ws.value.onclose = () => {
        console.log('WebSocket disconnected')
        isConnected.value = false
        stopPing()
        
        reconnectTimer = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 5000)
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      connectionError.value = error.message
    }
  }
  
  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    stopPing()
    
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }
  
  const subscribe = (tsCodes) => {
    if (!isConnected.value || !ws.value) return
    
    tsCodes.forEach(code => subscribedStocks.add(code))
    
    ws.value.send(JSON.stringify({
      action: 'subscribe',
      ts_codes: tsCodes
    }))
  }
  
  const unsubscribe = (tsCodes) => {
    if (!isConnected.value || !ws.value) return
    
    tsCodes.forEach(code => subscribedStocks.delete(code))
    
    ws.value.send(JSON.stringify({
      action: 'unsubscribe',
      ts_codes: tsCodes
    }))
  }
  
  const getPrice = (tsCode) => {
    if (!isConnected.value || !ws.value) return
    
    ws.value.send(JSON.stringify({
      action: 'get_price',
      ts_code: tsCode
    }))
  }
  
  const getSignal = (tsCode) => {
    if (!isConnected.value || !ws.value) return
    
    ws.value.send(JSON.stringify({
      action: 'get_signal',
      ts_code: tsCode
    }))
  }
  
  const startPing = () => {
    pingTimer = setInterval(() => {
      if (isConnected.value && ws.value) {
        ws.value.send(JSON.stringify({
          action: 'ping',
          timestamp: Date.now()
        }))
      }
    }, 30000)
  }
  
  const stopPing = () => {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    isConnected,
    lastMessage,
    subscribedStocks,
    connectionError,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    getPrice,
    getSignal
  }
}
