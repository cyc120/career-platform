import api from './client'

async function ensureToken() {
  let token = localStorage.getItem('access_token')
  if (!token) {
    const { data } = await api.post('/auth/guest-token')
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    token = data.access_token
  }
  return token
}

export const learningPlanApi = {
  generate(data) {
    return api.post('/learning-plan/generate', data, { timeout: 120000 })
  },
  polish(data) {
    return api.post('/learning-plan/polish', data)
  },
  dailyTasks(data) {
    return api.post('/learning-plan/daily-tasks', data, { timeout: 120000 })
  },
  adjust(data) {
    return api.post('/learning-plan/adjust', data)
  },
  export(data) {
    return api.post('/learning-plan/export', data)
  },
  coach(message, history = [], extra = {}) {
    return api.post('/learning-plan/coach', { message, history, ...extra }, { timeout: 60000 })
  },
  /**
   * Streaming coach - uses SSE for real-time token output.
   * @param {string} message
   * @param {Array} history
   * @param {Object} extra - { previous_radar_data, previous_details }
   * @param {Function} onToken - called with each token string
   * @param {Function} onRadar - called with { radar_data, dimension_details }
   * @param {Function} onDone - called when stream ends
   */
  async coachStream(message, history = [], extra = {}, onToken, onRadar, onDone) {
    console.log('[coachStream] Starting stream request...')
    const token = await ensureToken()
    // 直连后端，绕过 Vite proxy（proxy 会缓冲 SSE）
    const resp = await fetch('http://localhost:8000/api/v1/learning-plan/coach/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message, history, ...extra }),
    })

    if (!resp.ok) {
      throw new Error(`Stream request failed: ${resp.status}`)
    }
    console.log('[coachStream] Response OK, reading stream...')

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let doneCalled = false
    let eventCount = 0

    const processEvent = (eventData) => {
      const trimmed = eventData.trim()
      if (!trimmed) return
      // 提取 data: 行（一个事件可能有多行 data）
      const dataLines = trimmed.split('\n').filter(l => l.startsWith('data: '))
      if (dataLines.length === 0) return
      const dataStr = dataLines.map(l => l.slice(6)).join('\n')
      try {
        const data = JSON.parse(dataStr)
        eventCount++
        if (data.type === 'token') {
          onToken?.(data.content)
        }
        else if (data.type === 'radar') {
          console.log('[coachStream] RADAR event received! radar_data:', data.radar_data)
          console.log('[coachStream] dimension_details keys:', Object.keys(data.dimension_details || {}))
          onRadar?.(data)
          console.log('[coachStream] onRadar callback executed')
        }
        else if (data.type === 'done') {
          console.log('[coachStream] DONE event, total events:', eventCount)
          if (!doneCalled) { doneCalled = true; onDone?.() }
        }
      } catch (e) { console.warn('[coachStream] parse error:', e, 'raw:', dataStr.substring(0, 100)) }
    }

    // 从 buffer 中提取完整事件并处理
    const drainBuffer = () => {
      while (true) {
        const idx = buffer.indexOf('\n\n')
        if (idx === -1) break
        const event = buffer.substring(0, idx)
        buffer = buffer.substring(idx + 2)
        processEvent(event)
      }
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          if (buffer.trim()) processEvent(buffer)
          buffer = ''
          break
        }
        buffer += decoder.decode(value, { stream: true })
        drainBuffer()
      }
    } catch (e) {
      console.error('[coachStream] Stream read error:', e)
    }

    if (!doneCalled) { doneCalled = true; onDone?.() }
    console.log('[coachStream] Stream complete. Total events processed:', eventCount)
  },
  getTasks() {
    return api.get('/learning-plan/tasks')
  },
  updateTask(taskId, data) {
    return api.put(`/learning-plan/tasks/${taskId}`, data)
  },
  completeTask(taskId) {
    return api.post(`/learning-plan/tasks/${taskId}/complete`)
  },
}
