import api from './client'

export const favoritesApi = {
  list() {
    return api.get('/favorites')
  },
  add(jobId) {
    return api.post('/favorites', { job_id: jobId })
  },
  remove(jobId) {
    return api.delete(`/favorites/${jobId}`)
  },
}
