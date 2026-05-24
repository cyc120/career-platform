import api from './client'

export const matchingApi = {
  match(profileData) {
    return api.post('/matching/match', profileData || {}, { timeout: 120000 })
  },
  selectJob(jobData) {
    return api.post('/matching/select-job', { job_data: jobData }, { timeout: 120000 })
  },
  getSelectedJob() {
    return api.get('/matching/selected-job')
  },
  hasMatching() {
    return api.get('/matching/has-matching')
  },
  getCapabilityModel() {
    return api.get('/matching/capability-model')
  },
  getJobGraph(jobTitle) {
    return api.get('/matching/job-graph', { params: { job_title: jobTitle } })
  },
}
