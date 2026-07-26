<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">数据导入</h3>

    <el-alert title="导入说明" type="info" :closable="false" style="margin-bottom:16px">
      <p style="margin:4px 0">1. 请准备 CSV 格式文件（UTF-8 编码）</p>
      <p style="margin:4px 0">2. CSV 表头会自动匹配管理项的字段名称</p>
      <p style="margin:4px 0">3. 如果表头与字段名不匹配，则按列顺序导入</p>
    </el-alert>

    <el-form label-width="100px">
      <el-form-item label="目标管理项">
        <el-select v-model="targetCategoryId" placeholder="请选择要导入到的管理项" style="width:300px">
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
          :on-remove="() => file = null"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon> 选择CSV文件
          </el-button>
        </el-upload>
      </el-form-item>
      <el-form-item>
        <el-button type="success" @click="handleImport" :loading="importing" :disabled="!file || !targetCategoryId">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoryApi, importApi } from '../../api'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const categories = ref<any[]>([])
const targetCategoryId = ref<number | null>(null)
const file = ref<File | null>(null)
const importing = ref(false)
const lastResult = ref<any>(null)

onMounted(async () => {
  const res = await categoryApi.list()
  categories.value = res.data || []
})

function handleFileChange(uploadFile: any) {
  file.value = uploadFile.raw
}

async function handleImport() {
  if (!file.value || !targetCategoryId.value) return
  importing.value = true
  try {
    const res = await importApi.importCsv(targetCategoryId.value, file.value)
    lastResult.value = res.data
    ElMessage.success(`成功导入 ${res.data.imported} 条记录`)
  } finally {
    importing.value = false
  }
}
</script>
