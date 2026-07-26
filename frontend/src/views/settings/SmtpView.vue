<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">邮件设置</h3>
    <el-alert title="配置邮件服务器后，提醒将通过邮件发送，忘记密码时临时密码也将发送到收件邮箱" type="info" :closable="false" style="margin-bottom:16px" />
    <el-form :model="smtpForm" label-width="120px" style="max-width:500px">
      <el-form-item label="SMTP服务器">
        <el-input v-model="smtpForm.host" placeholder="如 smtp.qq.com" />
      </el-form-item>
      <el-form-item label="端口">
        <el-input-number v-model="smtpForm.port" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item label="发件邮箱">
        <el-input v-model="smtpForm.username" placeholder="发件邮箱账号" />
        <div style="color:#909399;font-size:12px;margin-top:4px">用于SMTP登录的发件邮箱地址</div>
      </el-form-item>
      <el-form-item label="密码/授权码">
        <el-input v-model="smtpForm.password" type="password" show-password placeholder="SMTP授权码" />
      </el-form-item>
      <el-form-item label="发件名称">
        <el-input v-model="smtpForm.from_addr" placeholder="发件人显示地址，默认为发件邮箱" />
      </el-form-item>
      <el-form-item label="收件邮箱">
        <el-input v-model="smtpForm.recipient_email" placeholder="用于接收提醒和密码找回邮件" />
        <div style="color:#909399;font-size:12px;margin-top:4px">提醒邮件和忘记密码的临时密码将发送到此地址</div>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSaveSmtp" :loading="savingSmtp">保存设置</el-button>
        <el-button @click="handleTestSmtp" :loading="testingSmtp" :disabled="!smtpForm.host">
          <el-icon><Message /></el-icon> 发送测试邮件
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { settingsApi } from '../../api'
import { ElMessage } from 'element-plus'
import { Message } from '@element-plus/icons-vue'

const savingSmtp = ref(false)
const testingSmtp = ref(false)

const smtpForm = reactive({
  host: '',
  port: 587,
  username: '',
  password: '',
  from_addr: '',
  recipient_email: ''
})

onMounted(async () => {
  try {
    const res = await settingsApi.getSmtp()
    if (res.data) {
      smtpForm.host = res.data.host || ''
      smtpForm.port = res.data.port || 587
      smtpForm.username = res.data.username || ''
      smtpForm.password = res.data.password || ''
      smtpForm.from_addr = res.data.from_addr || ''
      smtpForm.recipient_email = res.data.recipient_email || ''
    }
  } catch {}
})

async function handleSaveSmtp() {
  savingSmtp.value = true
  try {
    await settingsApi.updateSmtp(smtpForm)
    ElMessage.success('邮件配置已保存')
  } finally {
    savingSmtp.value = false
  }
}

async function handleTestSmtp() {
  testingSmtp.value = true
  try {
    await settingsApi.testSmtp()
    ElMessage.success('测试邮件已发送')
  } finally {
    testingSmtp.value = false
  }
}
</script>
