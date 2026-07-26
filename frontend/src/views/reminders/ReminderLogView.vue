<template>
  <div class="page-container">
    <div class="page-toolbar">
      <h3>提醒日志</h3>
      <div style="display:flex;gap:8px">
        <el-select v-model="filterCategoryId" placeholder="筛选管理项" clearable @change="fetchLogs" style="width:150px">
          <el-option v-for="cat in categories" :key="cat.id" :value="cat.id" :label="cat.name" />
        </el-select>
        <el-button type="primary" @click="triggerCheck" :loading="triggerLoading">手动检查提醒</el-button>
      </div>
    </div>

    <el-table :data="logs" border stripe v-loading="loading" empty-text="暂无提醒记录">
      <el-table-column prop="category_name" label="管理项" width="120" />
      <el-table-column prop="sent_at" label="发送时间" width="180" />
      <el-table-column prop="remind_type" label="提醒类型" width="90">
        <template #default="{ row }">
          <el-tag size="small">{{ typeLabel(row.remind_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="150" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'sent' ? 'success' : 'danger'" size="small">
            {{ row.status === 'sent' ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="error_msg" label="错误信息" min-width="120" show-overflow-tooltip />
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      style="margin-top:16px;justify-content:flex-end"
      layout="total, prev, pager, next"
      @change="fetchLogs"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { reminderApi, categoryApi } from '../../api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const triggerLoading = ref(false)
const logs = ref<any[]>([])
const categories = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterCategoryId = ref<number | null>(null)

onMounted(async () => {
  const catRes = await categoryApi.list()
  categories.value = catRes.data || []
  fetchLogs()
})

async function fetchLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, pageSize: pageSize.value }
    if (filterCategoryId.value) params.categoryId = filterCategoryId.value
    const res = await reminderApi.logs(params)
    logs.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

async function triggerCheck() {
  triggerLoading.value = true
  try {
    await reminderApi.trigger()
    ElMessage.success('提醒检查已触发')
    fetchLogs()
  } finally {
    triggerLoading.value = false
  }
}

function typeLabel(type: string) {
  const map: Record<string, string> = { once: '一次性', multi: '多次', recurring: '循环' }
  return map[type] || type
}
</script>
