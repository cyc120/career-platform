import api from './client'

export const jobsApi = {
  list(params = {}) {
    return api.get('/jobs', { params })
  },
  detail(id) {
    return api.get(`/jobs/${id}`)
  },
  search(q, params = {}) {
    return api.get('/jobs/search', { params: { q, ...params } })
  },
}
