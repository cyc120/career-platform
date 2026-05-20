import api from './client'

export const resumeApi = {
  extract(formData) {
    return api.post('/resume/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    })
  },
  supplement(data) {
    return api.post('/resume/supplement', data)
  },
  analyze(data) {
    return api.post('/resume/analyze', data)
  },
}
