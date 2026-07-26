<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">站点标题</h3>
    <el-form :model="form" label-width="120px" style="max-width:500px">
      <el-form-item label="当前标题">
        <span style="font-weight:500">{{ siteStore.title }}</span>
      </el-form-item>
      <el-form-item label="新标题">
        <el-input v-model="form.title" placeholder="如：我的数据管家" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSave" :loading="saving">保存标题</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { settingsApi } from '../../api'
import { useSiteStore } from '../../stores/site'
import { ElMessage } from 'element-plus'

const siteStore = useSiteStore()
const saving = ref(false)
const form = reactive({ title: '' })

onMounted(() => { form.title = siteStore.title })

async function handleSave() {
  if (!form.title.trim()) return
  saving.value = true
  try {
    await settingsApi.updateSite(form.title.trim())
    await siteStore.fetchTitle()
    ElMessage.success('标题已更新')
  } finally { saving.value = false }
}
</script>
