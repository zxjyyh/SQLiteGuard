import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../api/request'

export const useSiteStore = defineStore('site', () => {
  const title = ref('个人数据管家')

  async function fetchTitle() {
    try {
      const res = await request.get('/settings/site-title')
      title.value = res.data?.title || '个人数据管家'
      document.title = title.value
    } catch {}
  }

  return { title, fetchTitle }
})
