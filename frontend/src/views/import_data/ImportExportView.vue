<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">数据导入导出</h3>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="导入数据" name="import">
        <el-alert title="导入说明" type="info" :closable="false" style="margin-bottom:16px">
          <p style="margin:4px 0">1. 请准备 CSV 格式文件（UTF-8 编码）</p>
          <p style="margin:4px 0">2. CSV 表头会自动匹配管理项的字段名称</p>
          <p style="margin:4px 0">3. 如果表头与字段名不匹配，则按列顺序导入</p>
        </el-alert>

        <el-form label-width="100px">
          <el-form-item label="目标管理项">
            <el-select v-model="importCategoryId" placeholder="请选择要导入到的管理项" style="width:300px">
              <el-option v-for="cat in categories" :key="cat.id" :value="cat.id" :label="cat.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="选择文件">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".csv"
              :on-change="handleFileChange"
              :on-remove="() => importFile = null"
            >
              <el-button type="primary">
                <el-icon><Upload /></el-icon> 选择CSV文件
              </el-button>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="success" @click="handleImport" :loading="importing" :disabled="!importFile || !importCategoryId">
              <el-icon><Upload /></el-icon> 开始导入
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="lastResult" style="margin-top:16px">
          <el-alert :title="`成功导入 ${lastResult.imported} 条记录`" type="success" :closable="false" />
          <div v-if="lastResult.errors?.length" style="margin-top:8px">
            <p style="color:#E6A23C;margin-bottom:4px">导入异常：</p>
            <p v-for="(err, i) in lastResult.errors" :key="i" style="color:#909399;font-size:13px">{{ err }}</p>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="导出数据" name="export">
        <el-alert title="导出说明" type="info" :closable="false" style="margin-bottom:16px">
          <p style="margin:4px 0">1. 选择要导出的管理项</p>
          <p style="margin:4px 0">2. 导出为 CSV 格式，表头为字段中文名，兼容 Excel 打开</p>
        </el-alert>

        <el-form label-width="100px">
          <el-form-item label="导出管理项">
            <el-select v-model="exportCategoryId" placeholder="请选择要导出的管理项" style="width:300px">
              <el-option v-for="cat in categories" :key="cat.id" :value="cat.id" :label="`${cat.name}（${cat.field_count || 0}条）`" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleExport" :loading="exporting" :disabled="!exportCategoryId">
              <el-icon><Download /></el-icon> 导出CSV
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoryApi, importApi } from '../../api'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import request from '../../api/request'

const activeTab = ref('import')
const categories = ref<any[]>([])

// 导入
const importCategoryId = ref<number | null>(null)
const importFile = ref<File | null>(null)
const importing = ref(false)
const lastResult = ref<any>(null)

// 导出
const exportCategoryId = ref<number | null>(null)
const exporting = ref(false)

onMounted(async () => {
  const res = await categoryApi.list()
  categories.value = res.data || []
})

function handleFileChange(uploadFile: any) {
  importFile.value = uploadFile.raw
}

async function handleImport() {
  if (!importFile.value || !importCategoryId.value) return
  importing.value = true
  try {
    const res = await importApi.importCsv(importCategoryId.value, importFile.value)
    lastResult.value = res.data
    ElMessage.success(`成功导入 ${res.data.imported} 条记录`)
    // 刷新分类数据以更新记录数
    const catRes = await categoryApi.list()
    categories.value = catRes.data || []
  } finally {
    importing.value = false
  }
}

async function handleExport() {
  if (!exportCategoryId.value) return
  exporting.value = true
  try {
    const response = await request.get(`/import/csv/${exportCategoryId.value}`, {
      responseType: 'blob'
    })
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }))
    const link = document.createElement('a')
    link.href = url

    // 从响应头获取文件名
    const disposition = response.headers?.['content-disposition'] || response.headers?.['Content-Disposition']
    let filename = 'export.csv'
    if (disposition) {
      const match = disposition.match(/filename="?(.+?)"?$/i)
      if (match) filename = decodeURIComponent(match[1])
    } else {
      const cat = categories.value.find(c => c.id === exportCategoryId.value)
      if (cat) filename = `${cat.name}.csv`
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
  } finally {
    exporting.value = false
  }
}
</script>
