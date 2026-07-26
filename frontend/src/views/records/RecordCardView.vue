<template>
  <div class="card-list" v-loading="loading" element-loading-text="加载中...">
    <div v-if="records.length === 0" class="empty-tip">暂无数据</div>
    <div
      v-for="(row, idx) in records"
      :key="row.id"
      :class="['data-card', { 'card-selected': row.id === selectedId }]"
      @click="$emit('select', row.id)"
    >
      <div class="card-header">
        <span class="card-index">#{{ idx + 1 }}</span>
        <el-icon v-if="row._hasReminder" color="#E6A23C"><Bell /></el-icon>
      </div>
      <div class="card-body">
        <div v-for="field in fields" :key="field.field_key" class="card-field" @dblclick.stop="startEdit(row.id, field.field_key)">
          <span class="field-label">{{ field.field_label }}</span>
          <div v-if="editingCell?.rowId === row.id && editingCell?.fieldKey === field.field_key" class="field-edit">
            <input
              v-model="tempEditValue"
              class="inline-input"
              @blur="commitEdit(row.id, field.field_key)"
              @keyup.enter="commitEdit(row.id, field.field_key)"
              @click.stop
              ref="cardInput"
            />
          </div>
          <span v-else class="field-value val-clickable">
            {{ getEditValue(row.id, field.field_key, row[field.field_key]) || '-' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { Bell } from '@element-plus/icons-vue'

const props = defineProps<{
  records: any[]
  fields: any[]
  loading: boolean
  selectedId: number | null
}>()

const emit = defineEmits<{
  select: [id: number]
  edit: [row: any]
  delete: [id: number]
  dblclick: [row: any, column: any, cell: any, event: any]
  cellEdit: [rowId: number, fieldKey: string, value: string]
}>()

const editingCell = ref<{ rowId: number; fieldKey: string } | null>(null)
const tempEditValue = ref('')

function getEditValue(rowId: number, fieldKey: string, original: string) {
  // editingCell管理卡片模式的当前编辑状态
  return editingCell.value?.rowId === rowId && editingCell.value?.fieldKey === fieldKey ? tempEditValue.value : original
}

function startEdit(rowId: number, fieldKey: string) {
  const row = props.records.find(r => r.id === rowId)
  if (!row) return
  tempEditValue.value = row[fieldKey] || ''
  editingCell.value = { rowId, fieldKey }
  nextTick(() => {
    const el = document.querySelector('.inline-input') as HTMLInputElement
    el?.focus()
    el?.select()
  })
}

function commitEdit(rowId: number, fieldKey: string) {
  const value = tempEditValue.value
  emit('cellEdit', rowId, fieldKey, value)
  editingCell.value = null
}
</script>

<style scoped>
.card-list { padding: 4px 0; }
.data-card {
  background: #fff; border-radius: 8px; margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; cursor: pointer;
  transition: box-shadow 0.2s;
}
.data-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.12); }
.card-selected { box-shadow: 0 0 0 2px #409EFF; }
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; border-bottom: 1px solid #f0f0f0;
}
.card-index { font-weight: 600; color: #909399; font-size: 13px; }
.card-body { padding: 8px 14px; }
.card-field {
  display: flex; padding: 6px 0;
  border-bottom: 1px dashed #f5f5f5;
}
.card-field:last-child { border-bottom: none; }
.field-label {
  flex-shrink: 0; width: 70px; color: #909399; font-size: 13px;
}
.field-value {
  flex: 1; color: #303133; font-size: 14px; word-break: break-all;
}
.val-clickable {
  cursor: pointer; padding: 2px 6px; border-radius: 2px;
}
.val-clickable:hover { background: #f0f5ff; }
.field-edit { flex: 1; }
.inline-input {
  width: 100%; border: 1px solid #409EFF; border-radius: 3px;
  padding: 3px 6px; font-size: 14px; outline: none; box-sizing: border-box;
}
.empty-tip { text-align: center; color: #c0c4cc; padding: 40px 0; font-size: 14px; }
</style>
