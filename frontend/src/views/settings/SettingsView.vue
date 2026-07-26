<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">系统设置</h3>

    <el-tabs>
      <el-tab-pane label="修改密码">
        <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="120px" style="max-width:400px">
          <el-form-item label="原密码" prop="oldPassword">
            <el-input v-model="pwdForm.oldPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="pwdForm.newPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="pwdForm.confirmPassword" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleChangePwd" :loading="changingPwd">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="邮件设置">
        <el-alert title="配置邮件服务器后，提醒将通过邮件发送" type="info" :closable="false" style="margin-bottom:16px" />
        <el-form :model="smtpForm" label-width="120px" style="max-width:500px">
          <el-form-item label="SMTP服务器">
            <el-input v-model="smtpForm.host" placeholder="如 smtp.qq.com" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="smtpForm.port" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="邮箱账号">
            <el-input v-model="smtpForm.username" placeholder="your@email.com" />
          </el-form-item>
          <el-form-item label="密码/授权码">
            <el-input v-model="smtpForm.password" type="password" show-password placeholder="SMTP授权码" />
          </el-form-item>
          <el-form-item label="发件地址">
            <el-input v-model="smtpForm.from_addr" placeholder="默认与邮箱账号相同" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSaveSmtp" :loading="savingSmtp">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { authApi, settingsApi } from '../../api'
import { ElMessage } from 'element-plus'

const pwdFormRef = ref()
const changingPwd = ref(false)
const savingSmtp = ref(false)

const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPwd = (_rule: any, value: string, callback: any) => {
  if (value !== pwdForm.newPassword) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ]
}

const smtpForm = reactive({
  host: '',
  port: 587,
  username: '',
  password: '',
  from_addr: ''
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
    }
  } catch {}
})

async function handleChangePwd() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  changingPwd.value = true
  try {
    await authApi.changePassword(pwdForm.oldPassword, pwdForm.newPassword)
    ElMessage.success('密码修改成功')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirmPassword = ''
  } finally {
    changingPwd.value = false
  }
}

async function handleSaveSmtp() {
  savingSmtp.value = true
  try {
    await settingsApi.updateSmtp(smtpForm)
    ElMessage.success('邮件配置已保存')
  } finally {
    savingSmtp.value = false
  }
}
</script>
