import api from './client'

export const matchingApi = {
  match(profileData) {
    return api.post('/matching/match', profileData || {}, { timeout: 120000 })
  },
}
