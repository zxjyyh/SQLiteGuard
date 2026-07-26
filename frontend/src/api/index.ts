import request from './request'

export { authApi } from './auth'

export const categoryApi = {
  list: () => request.get('/categories'),
  create: (data: any) => request.post('/categories', data),
  update: (id: number, data: any) => request.put(`/categories/${id}`, data),
  delete: (id: number) => request.delete(`/categories/${id}`),
  getFields: (id: number) => request.get(`/categories/${id}/fields`)
}

export const recordApi = {
  list: (categoryId: number, params: any) =>
    request.get(`/records/${categoryId}`, { params }),
  get: (categoryId: number, recordId: number) =>
    request.get(`/records/${categoryId}/${recordId}`),
  create: (categoryId: number, data: any) =>
    request.post(`/records/${categoryId}`, data),
  update: (categoryId: number, recordId: number, data: any) =>
    request.put(`/records/${categoryId}/${recordId}`, data),
  delete: (categoryId: number, recordId: number) =>
    request.delete(`/records/${categoryId}/${recordId}`)
}

export const reminderApi = {
  logs: (params: any) => request.get('/reminders/logs', { params }),
  stats: () => request.get('/reminders/stats'),
  trigger: () => request.post('/reminders/test'),
  pending: () => request.get('/reminders/pending')
}

export const dashboardApi = {
  stats: () => request.get('/dashboard/stats')
}

export const settingsApi = {
  getSmtp: () => request.get('/settings/smtp'),
  updateSmtp: (data: any) => request.put('/settings/smtp', data),
  testSmtp: () => request.post('/settings/smtp/test'),
  getSite: () => request.get('/settings/site'),
  updateSite: (site_title: string) => request.put('/settings/site', { site_title })
}

export const importApi = {
  importCsv: (categoryId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request.post(`/import/csv/${categoryId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
