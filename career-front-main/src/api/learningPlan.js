import api from './client'

export const learningPlanApi = {
  generate(data) {
    return api.post('/learning-plan/generate', data, { timeout: 120000 })
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
  coach(message, history = [], extra = {}) {
    return api.post('/learning-plan/coach', { message, history, ...extra }, { timeout: 60000 })
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
