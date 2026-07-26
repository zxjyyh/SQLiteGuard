<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">仪表盘</h3>

    <div class="card-grid">
      <el-card v-for="cat in stats.categories" :key="cat.id" shadow="hover"
        @click="$router.push(`/category/${cat.id}`)" style="cursor:pointer">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="32"><component :is="cat.icon || 'Folder'" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ cat.total }}</div>
            <div class="stat-label">{{ cat.name }}</div>
            <div class="stat-reminder" v-if="cat.activeReminders > 0">
              <el-icon size="14"><Bell /></el-icon>
              {{ cat.activeReminders }} 个待提醒
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 提醒概览 -->
    <el-card style="margin-top:20px">
      <template #header>
        <div class="overview-header">
          <span>提醒概览</span>
          <div class="overview-actions">
            <el-button size="small" @click="togglePending" :icon="pendingExpanded ? ArrowUp : ArrowDown">
              {{ pendingExpanded ? '收起提醒事项' : '查看提醒事项' }}
            </el-button>
            <el-button size="small" @click="triggerCheck" :loading="triggerLoading">手动检查</el-button>
          </div>
        </div>
      </template>
      <div class="overview-stats">
        <div class="overview-item">
          <div class="ov-value" style="color:#409EFF">{{ stats.pendingCount }}</div>
          <div class="ov-label">待提醒数量</div>
        </div>
      </div>

      <!-- 待提醒列表（默认展开） -->
      <div v-show="pendingExpanded" class="pending-panel">
        <el-divider style="margin:12px 0" />
        <el-table :data="pendingList" size="small" max-height="360" empty-text="暂无待提醒事项" v-loading="pendingLoading">
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.next_remind_at <= now ? 'danger' : ''">
                {{ row.next_remind_at <= now ? '已到期' : '进行中' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="category_name" label="管理项" width="100" />
          <el-table-column label="提醒时间" width="160">
            <template #default="{ row }">{{ (row.next_remind_at || '').slice(0, 16) }}</template>
          </el-table-column>
          <el-table-column prop="note" label="备注" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.note || '-' }}</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { dashboardApi, reminderApi } from '../../api'
import { ElMessage } from 'element-plus'
import { Bell, ArrowUp, ArrowDown } from '@element-plus/icons-vue'

const stats = reactive<any>({ categories: [], pendingCount: 0 })
const triggerLoading = ref(false)
const pendingExpanded = ref(true)
const pendingLoading = ref(false)
const pendingList = ref<any[]>([])
const now = new Date().toISOString().slice(0, 16).replace('T', ' ')

onMounted(async () => {
  const [dashRes] = await Promise.all([
    dashboardApi.stats(),
    loadPending()
  ])
  Object.assign(stats, dashRes.data)
})

async function loadPending() {
  pendingLoading.value = true
  try {
    const res = await reminderApi.pending()
    pendingList.value = res.data || []
  } finally {
    pendingLoading.value = false
  }
}

async function togglePending() {
  pendingExpanded.value = !pendingExpanded.value
  if (pendingExpanded.value && pendingList.value.length === 0) {
    await loadPending()
  }
}

async function triggerCheck() {
  triggerLoading.value = true
  try {
    await reminderApi.trigger()
    ElMessage.success('提醒检查已触发')
    const [dashRes] = await Promise.all([
      dashboardApi.stats(),
      loadPending()
    ])
    Object.assign(stats, dashRes.data)
  } catch {} finally {
    triggerLoading.value = false
  }
}
</script>

<style scoped>
.stat-card { display: flex; align-items: center; gap: 16px; }
.stat-icon {
  width: 56px; height: 56px; display: flex; align-items: center; justify-content: center;
  background: #ecf5ff; border-radius: 12px; color: #409EFF;
}
.stat-value { font-size: 24px; font-weight: 600; color: #303133; }
.stat-label { font-size: 14px; color: #909399; }
.stat-reminder { font-size: 12px; color: #E6A23C; margin-top: 4px; display: flex; align-items: center; gap: 4px; }

.overview-header { display: flex; justify-content: space-between; align-items: center; }
.overview-actions { display: flex; gap: 8px; }

.overview-stats { display: flex; gap: 40px; }
.overview-item { text-align: center; }
.ov-value { font-size: 28px; font-weight: 600; height: 38px; line-height: 38px; }
.ov-label { font-size: 13px; color: #909399; margin-top: 4px; }

.pending-panel { margin-top: 4px; }
</style>
