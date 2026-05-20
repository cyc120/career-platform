import api from './client'

export const learningPlanApi = {
  generate(data) {
    return api.post('/learning-plan', data, { timeout: 120000 })
  },
  polish(data) {
    return api.post('/learning-plan/polish', data)
  },
  dailyTasks(data) {
    return api.post('/learning-plan/daily-tasks', data)
  },
  adjust(data) {
    return api.post('/learning-plan/adjust', data)
  },
  export(data) {
    return api.post('/learning-plan/export', data)
  },
}
