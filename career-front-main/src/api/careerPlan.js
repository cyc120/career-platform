import api from './client'

export const careerPlanApi = {
  generate() {
    return api.post('/career-plan', {}, { timeout: 120000 })
  },
}
