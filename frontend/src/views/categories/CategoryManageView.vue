<template>
  <div class="page-container">
    <div class="page-toolbar">
      <h3>数据库管理</h3>
      <div style="display:flex;gap:6px;align-items:center">
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon> 新增管理项
        </el-button>
        <el-button @click="openEdit" :disabled="!selectedId">
          <el-icon><Edit /></el-icon> 编辑管理项
        </el-button>
        <el-popconfirm title="确定要删除此管理项吗？所有数据将一并删除！" @confirm="handleDeleteClick" :disabled="!selectedId">
          <template #reference>
            <el-button type="danger" :disabled="!selectedId">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <el-table :data="categories" border stripe v-loading="loading" empty-text="暂无管理项"
      @row-click="selectRow" @row-dblclick="openEdit" :row-class-name="rowClass">
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="图标" width="70" align="center">
        <template #default="{ row }">
          <el-icon size="18"><component :is="row.icon || 'Folder'" /></el-icon>
        </template>
      </el-table-column>
      <el-table-column prop="field_count" label="字段数" width="70" align="center" />
      <el-table-column prop="has_reminder" label="提醒" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.has_reminder ? 'success' : 'info'" size="small">
            {{ row.has_reminder ? '已启用' : '未启用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
    </el-table>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑管理项' : '新增管理项'" width="580px" :close-on-click-modal="false" @closed="resetDialog">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：账号信息" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="可选的描述信息" />
        </el-form-item>
        <el-form-item label="图标" prop="icon">
          <div style="display:flex;align-items:center;gap:12px">
            <el-select v-model="form.icon" style="width:200px">
              <el-option v-for="icon in iconList" :key="icon" :value="icon">
                <span style="display:flex;align-items:center;gap:8px">
                  <el-icon size="16"><component :is="icon" /></el-icon>
                  <span>{{ icon }}</span>
                </span>
              </el-option>
            </el-select>
            <div class="icon-preview">
              <el-icon size="28"><component :is="form.icon || 'Folder'" /></el-icon>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="启用提醒">
          <el-switch v-model="form.hasReminder" />
        </el-form-item>
        <el-divider content-position="left">自定义字段</el-divider>
        <div v-for="(field, index) in form.fields" :key="index" style="display:flex;gap:8px;margin-bottom:12px;align-items:center">
          <el-input v-model="field.label" :placeholder="`字段名称 ${index + 1}`" style="flex:1" />
          <el-button type="danger" :icon="Delete" circle size="small" @click="form.fields.splice(index, 1)"
            :disabled="form.fields.length <= 1" />
        </div>
        <el-button type="primary" text @click="form.fields.push({ label: '' })">
          <el-icon><Plus /></el-icon> 添加字段
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingId ? '保存修改' : '确定创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { categoryApi } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus, Edit } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const categories = ref<any[]>([])
const selectedId = ref<number | null>(null)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref()
const originalFields = ref<any[]>([])

const form = reactive({
  name: '', description: '', icon: 'Folder', hasReminder: false, fields: [{ label: '' }]
})

const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }
const iconList = ['Folder', 'User', 'Lock', 'Notebook', 'Link', 'VideoPlay', 'Headset', 'Collection', 'Memo', 'Document', 'Clock', 'Star', 'Setting', 'DataBoard', 'Odometer', 'Tools']

function rowClass({ row }: any) { return row.id === selectedId.value ? 'selected-row' : '' }
function selectRow(row: any) { selectedId.value = row.id }

function openCreate() {
  editingId.value = null
  form.name = ''; form.description = ''; form.icon = 'Folder'; form.hasReminder = false; form.fields = [{ label: '' }]
  originalFields.value = []
  dialogVisible.value = true
}

async function openEdit() {
  if (!selectedId.value) return
  const cat = categories.value.find(c => c.id === selectedId.value)
  if (!cat) return

  editingId.value = cat.id
  form.name = cat.name
  form.description = cat.description || ''
  form.icon = cat.icon || 'Folder'
  form.hasReminder = !!cat.has_reminder

  // 加载字段
  const res = await categoryApi.getFields(cat.id)
  const fields = (res.data || []).map((f: any) => ({ label: f.field_label }))
  if (fields.length === 0) fields.push({ label: '' })
  form.fields = fields
  originalFields.value = JSON.parse(JSON.stringify(fields))
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  const validFields = form.fields.filter((f: any) => f.label.trim())
  if (validFields.length === 0) {
    ElMessage.warning('至少需要一个字段')
    return
  }

  // 如果是编辑且字段有变化，先确认
  if (editingId.value) {
    const fieldsChanged = JSON.stringify(validFields.map((f: any) => f.label)) !==
                          JSON.stringify(originalFields.value.map((f: any) => f.label))
    if (fieldsChanged) {
      try {
        await ElMessageBox.confirm(
          '修改自定义字段会删除此管理项中原有数据（同名字段数据会保留），确定继续吗？',
          '警告',
          { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
        )
      } catch {
        return // 用户取消
      }
    }
  }

  submitting.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      icon: form.icon,
      hasReminder: form.hasReminder,
      fields: validFields,
    }

    if (editingId.value) {
      // 判断字段是否有变化
      const changed = JSON.stringify(validFields.map((f: any) => f.label)) !==
                      JSON.stringify(originalFields.value.map((f: any) => f.label))
      await categoryApi.update(editingId.value, { ...payload, _fieldsChanged: changed })
      ElMessage.success('修改成功')
    } else {
      await categoryApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    selectedId.value = null
    await fetchCategories()
  } finally { submitting.value = false }
}

async function handleDeleteClick() {
  if (!selectedId.value) return
  try {
    await categoryApi.delete(selectedId.value)
    ElMessage.success('删除成功')
    selectedId.value = null
    await fetchCategories()
  } catch {}
}

function resetDialog() {
  editingId.value = null
  originalFields.value = []
}

onMounted(fetchCategories)
async function fetchCategories() {
  loading.value = true
  try {
    const res = await categoryApi.list()
    categories.value = res.data || []
  } finally { loading.value = false }
}
</script>

<style scoped>
:deep(.selected-row) { background-color: #ecf5ff !important; }
:deep(.selected-row:hover > td) { background-color: #d9ecff !important; }
.icon-preview {
  width: 44px; height: 44px; display: flex; align-items: center; justify-content: center;
  background: #ecf5ff; border-radius: 8px; color: #409EFF; flex-shrink: 0;
}
</style>
