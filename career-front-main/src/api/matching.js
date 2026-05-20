import api from './client'

export const matchingApi = {
  match() {
    return api.post('/matching/match', {}, { timeout: 120000 })
  },
}
