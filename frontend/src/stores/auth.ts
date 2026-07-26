import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  async function login(user: string, pwd: string) {
    const res = await authApi.login(user, pwd)
    token.value = res.data.token
    username.value = res.data.username
    localStorage.setItem('token', token.value)
    localStorage.setItem('username', username.value)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }

  return { token, username, login, logout }
})
