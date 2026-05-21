import api from './client'

export const agentsApi = {
  list() {
    return api.get('/agents')
  },
}
