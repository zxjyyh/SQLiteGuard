import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => {
    // 文件下载等 blob 响应直接放行
    if (response.config.responseType === 'blob' || response.config.responseType === 'arraybuffer') {
      return response
    }
    const data = response.data
    if (data.code !== 0) {
      if (data.code === -2) {
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        router.push('/login')
      }
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  error => {
    ElMessage.error('网络错误')
    return Promise.reject(error)
  }
)

export default request
