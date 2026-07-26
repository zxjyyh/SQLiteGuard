<template>
  <div class="page-container">
    <div class="page-toolbar">
      <div class="toolbar-title">
        <el-button @click="$router.push('/dashboard')" text>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ categoryName }}</h3>
        <span v-if="selectedId" style="color:#409EFF;font-size:13px">
          已选中 #{{ selectedId }}
        </span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索..." clearable size="small" style="width:160px" @clear="fetchData" @keyup.enter="fetchData" />
        <el-button size="small" @click="fetchData"><el-icon><Search /></el-icon></el-button>
        <el-button size="small" type="primary" @click="openCreateDialog"><el-icon><Plus /></el-icon> <span class="btn-text">新增</span></el-button>
        <el-button size="small" @click="handleEditClick" :disabled="!selectedId"><el-icon><Edit /></el-icon> <span class="btn-text">编辑</span></el-button>
        <el-popconfirm title="确定删除？" @confirm="handleDeleteClick" :disabled="!selectedId">
          <template #reference>
            <el-button size="small" type="danger" :disabled="!selectedId"><el-icon><Delete /></el-icon> <span class="btn-text">删除</span></el-button>
          </template>
        </el-popconfirm>
        <el-button size="small" type="success" @click="handleSaveClick" :loading="saving" :disabled="!hasChanges">
          <el-icon><Select /></el-icon> <span class="btn-text">保存</span>
        </el-button>
        <el-button size="small" @click="viewMode = viewMode === 'table' ? 'card' : 'table'">
          <el-icon><List v-if="viewMode==='table'" /><Grid v-else /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 表格模式 -->
    <el-table v-if="viewMode === 'table'" :data="records" border stripe v-loading="loading" empty-text="暂无数据"
      @sort-change="handleSortChange" table-layout="auto"
      @row-click="selectRow" :row-class-name="rowClass"
      @cell-dblclick="startInlineEdit">
      <el-table-column type="index" label="序号" width="55" />
      <el-table-column
        v-for="field in fields"
        :key="field.field_key"
        :prop="field.field_key"
        :label="field.field_label"
        sortable
        min-width="100"
        show-overflow-tooltip
        resizable
      >
        <template #default="{ row, column, $index }">
          <div v-if="isEditingCell(row.id, field.field_key)" class="inline-edit-cell">
            <el-input
              v-model="editMap[ row.id ][field.field_key]"
              size="small"
              @blur="endInlineEdit"
              @keyup.enter="endInlineEdit"
              ref="inlineInput"
              autofocus
            />
          </div>
          <span v-else class="cell-value">{{ row[field.field_key] || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="提醒" width="60" align="center">
        <template #default="{ row }">
          <el-icon v-if="row._hasReminder" color="#E6A23C"><Bell /></el-icon>
          <span v-else style="color:#C0C4CC">-</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 卡片模式 -->
    <RecordCardView
      v-if="viewMode === 'card'"
      :records="records"
      :fields="fields"
      :loading="loading"
      :selected-id="selectedId"
      @select="selectRowById"
      @edit="handleEditClick"
      @delete="handleDeleteClick"
      @dblclick="startInlineEdit"
      @cell-edit="onCardCellEdit"
    />

    <div style="margin-top:16px;display:flex;justify-content:flex-end">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[50, 100, 200]"
        layout="total, sizes, prev, pager, next"
        @change="fetchData"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" :close-on-click-modal="false" @closed="resetForm">
      <el-form :model="recordForm" ref="recordFormRef" label-width="120px">
        <el-form-item v-for="field in fields" :key="field.field_key" :label="field.field_label">
          <el-input v-model="recordForm[field.field_key]" :placeholder="`请输入${field.field_label}`" />
        </el-form-item>
        <el-divider content-position="left"><el-icon><Bell /></el-icon> 提醒设置</el-divider>
        <el-form-item label="启用提醒">
          <el-switch v-model="reminderForm.enabled" />
        </el-form-item>
        <template v-if="reminderForm.enabled">
          <el-form-item label="提醒类型">
            <el-radio-group v-model="reminderForm.type">
              <el-radio value="once">一次性</el-radio>
              <el-radio value="multi">多次</el-radio>
              <el-radio value="recurring">循环</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="reminderForm.type === 'once'" label="提醒时间">
            <el-date-picker v-model="reminderForm.remindAt" type="datetime" placeholder="选择提醒时间"
              format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm:ss" />
          </el-form-item>
          <template v-if="reminderForm.type === 'multi'">
            <el-form-item label="提醒频率(天)"><el-input-number v-model="reminderForm.intervalDays" :min="1" :max="3650" /></el-form-item>
            <el-form-item label="提醒次数"><el-input-number v-model="reminderForm.totalCount" :min="1" :max="1000" /></el-form-item>
          </template>
          <el-form-item v-if="reminderForm.type === 'recurring'" label="间隔天数">
            <el-input-number v-model="reminderForm.intervalDays" :min="1" :max="3650" />
          </el-form-item>
          <el-form-item label="备注"><el-input v-model="reminderForm.note" placeholder="提醒备注" /></el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          {{ editingId ? '保存修改' : '确认新增' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { categoryApi, recordApi } from '../../api'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Bell, Plus, Search, Edit, Delete, Select, List, Grid } from '@element-plus/icons-vue'
import RecordCardView from './RecordCardView.vue'

const route = useRoute()
const router = useRouter()
const categoryId = computed(() => Number(route.params.id))
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)
const viewMode = ref<'table' | 'card'>(isMobile.value ? 'card' : 'table')

const loading = ref(false)
const saving = ref(false)
const categoryName = ref('')
const fields = ref<any[]>([])
const records = ref<any[]>([])
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const keyword = ref('')
const selectedId = ref<number | null>(null)

// 行内编辑状态
const editingCell = ref<{ rowId: number; fieldKey: string } | null>(null)
const editMap = reactive<Record<number, Record<string, string>>>({})

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const recordFormRef = ref()
const recordForm = reactive<Record<string, string>>({})
const reminderForm = reactive({
  enabled: false, type: 'once', remindAt: '', intervalDays: 30, totalCount: 6, note: ''
})

const dialogTitle = computed(() => editingId.value ? '编辑记录' : '新增记录')

const hasChanges = computed(() => Object.keys(editMap).length > 0)

function rowClass({ row }: any) {
  return row.id === selectedId.value ? 'selected-row' : ''
}

// 选中行
function selectRow(row: any) { selectedId.value = row.id }
function selectRowById(id: number) { selectedId.value = id }

function isEditingCell(rowId: number, fieldKey: string) {
  return editingCell.value?.rowId === rowId && editingCell.value?.fieldKey === fieldKey
}

function startInlineEdit(row: any, column: any, _cell: any, _event: any) {
  if (!column?.property) return
  selectedId.value = row.id
  const fieldKey = column.property
  if (!editMap[row.id]) editMap[row.id] = {}
  if (editMap[row.id][fieldKey] === undefined) {
    editMap[row.id][fieldKey] = row[fieldKey] || ''
  }
  editingCell.value = { rowId: row.id, fieldKey }
  nextTick(() => {
    const inputs = document.querySelectorAll('.inline-edit-cell .el-input__inner')
    const last = inputs[inputs.length - 1] as HTMLInputElement
    last?.focus()
    last?.select()
  })
}

function endInlineEdit() { editingCell.value = null }

function onCardCellEdit(rowId: number, fieldKey: string, value: string) {
  if (!editMap[rowId]) editMap[rowId] = {}
  editMap[rowId][fieldKey] = value
}

// 编辑按钮 - 打开对话框
function handleEditClick() {
  if (!selectedId.value) return
  const row = records.value.find(r => r.id === selectedId.value)
  if (!row) return
  editingId.value = row.id
  for (const f of fields.value) recordForm[f.field_key] = row[f.field_key] || ''
  if (row._reminder) {
    reminderForm.enabled = true
    reminderForm.type = row._reminder.remind_type || 'once'
    reminderForm.remindAt = row._reminder.remind_at || ''
    reminderForm.intervalDays = row._reminder.interval_days || 30
    reminderForm.totalCount = row._reminder.total_count || 6
    reminderForm.note = row._reminder.note || ''
  }
  dialogVisible.value = true
}

// 删除按钮
async function handleDeleteClick() {
  if (!selectedId.value) return
  await recordApi.delete(categoryId.value, selectedId.value)
  ElMessage.success('删除成功')
  selectedId.value = null
  fetchData()
}

// 保存按钮 - 保存所有行内编辑
async function handleSaveClick() {
  if (!hasChanges.value) return
  saving.value = true
  try {
    for (const [rowId, changes] of Object.entries(editMap)) {
      await recordApi.update(categoryId.value, Number(rowId), changes)
    }
    ElMessage.success('保存成功')
    // 清空编辑
    for (const k of Object.keys(editMap)) delete editMap[Number(k)]
    fetchData()
  } catch {} finally {
    saving.value = false
  }
}

function openCreateDialog() {
  editingId.value = null
  selectedId.value = null
  resetForm()
  dialogVisible.value = true
}

function resetForm() {
  for (const f of fields.value) recordForm[f.field_key] = ''
  reminderForm.enabled = false; reminderForm.type = 'once'; reminderForm.remindAt = ''
  reminderForm.intervalDays = 30; reminderForm.totalCount = 6; reminderForm.note = ''
}

async function handleSave() {
  const data: any = { ...recordForm }
  data._reminder = { enabled: reminderForm.enabled, type: reminderForm.type, remindAt: reminderForm.remindAt, intervalDays: reminderForm.intervalDays, totalCount: reminderForm.totalCount, note: reminderForm.note }
  saving.value = true
  try {
    if (editingId.value) {
      await recordApi.update(categoryId.value, editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await recordApi.create(categoryId.value, data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

function onResize() { windowWidth.value = window.innerWidth }

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await loadCategoryInfo()
  fetchData()
})
onUnmounted(() => { window.removeEventListener('resize', onResize) })
watch(isMobile, (m) => { viewMode.value = m ? 'card' : 'table' })
watch(() => route.params.id, async () => { await loadCategoryInfo(); fetchData(); selectedId.value = null })

async function loadCategoryInfo() {
  try {
    const res = await categoryApi.getFields(categoryId.value)
    fields.value = res.data || []
    const catRes = await categoryApi.list()
    const cat = (catRes.data || []).find((c: any) => c.id === categoryId.value)
    categoryName.value = cat?.name || '数据列表'
  } catch {}
}

async function fetchData() {
  loading.value = true
  try {
    const res = await recordApi.list(categoryId.value, { page: page.value, pageSize: pageSize.value, keyword: keyword.value })
    records.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function handleSortChange() {}
</script>

<style scoped>
.toolbar-title { display: flex; align-items: center; gap: 8px; }
.toolbar-title h3 { margin: 0; font-size: 16px; }
.toolbar-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

:deep(.selected-row) { background-color: #ecf5ff !important; }
:deep(.selected-row:hover > td) { background-color: #d9ecff !important; }

.cell-value { cursor: pointer; display: block; min-height: 20px; padding: 0 4px; }
.cell-value:hover { background: #f0f5ff; border-radius: 2px; }
.inline-edit-cell { padding: 0; }
.inline-edit-cell :deep(.el-input__inner) { height: 28px; }

@media (max-width: 767px) {
  .page-toolbar { flex-wrap: wrap; gap: 8px; }
  .toolbar-actions { width: 100%; }
  .toolbar-actions .el-input { flex: 1; }
  .btn-text { display: none; }
}
</style>
