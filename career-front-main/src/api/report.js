import api from './client'

export const reportApi = {
  generate() {
    return api.post('/report/generate', {}, { timeout: 180000 })
  },
  polish(feedback) {
    return api.post('/report/polish', { feedback }, { timeout: 180000 })
  },
  load() {
    return api.get('/report/load')
  },
  exportFile(format) {
    return api.post('/report/export', { format }, { responseType: 'blob' })
  },
}
