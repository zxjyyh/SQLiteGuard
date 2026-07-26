import request from './request'

export const authApi = {
  login: (username: string, password: string) =>
    request.post('/auth/login', { username, password }),

  getProfile: () =>
    request.get('/auth/profile'),

  changePassword: (oldPassword: string, newPassword: string) =>
    request.put('/auth/password', { oldPassword, newPassword }),

  changeUsername: (username: string) =>
    request.put('/auth/username', { username }),

  forgotPassword: (username: string) =>
    request.post('/auth/forgot-password', { username }),

  getSmtpInfo: () =>
    request.get('/auth/smtp-info')
}
