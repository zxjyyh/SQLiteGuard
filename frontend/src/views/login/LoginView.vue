<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2>{{ siteStore.title }}</h2>
      <p class="subtitle">登录以管理你的数据</p>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width:100%">
            登 录
          </el-button>
        </el-form-item>
        <div style="text-align:center">
          <el-button type="primary" link @click="handleForgotPassword" :loading="forgotLoading">忘记密码</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useSiteStore } from '../../stores/site'
import { authApi } from '../../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const formRef = ref()
const loading = ref(false)
const forgotLoading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch {
  } finally {
    loading.value = false
  }
}

async function handleForgotPassword() {
  forgotLoading.value = true
  try {
    const smtpRes = await authApi.getSmtpInfo()
    const smtpInfo = smtpRes.data

    if (!smtpInfo.configured) {
      ElMessage.warning('邮件服务未配置')
      return
    }

    // 先让用户输入用户名
    const { value: inputUser } = await ElMessageBox.prompt(
      `系统将发送临时密码到 ${smtpInfo.email}，请输入要找回密码的用户名：`,
      '找回密码',
      { confirmButtonText: '下一步', cancelButtonText: '取消', inputPlaceholder: '请输入用户名' }
    )
    if (!inputUser?.trim()) return

    // 确认发送
    await ElMessageBox.confirm(
      `确认发送临时密码到 ${smtpInfo.email}？\n\n用户名：${inputUser}\n当前密码将被重置为随机密码。`,
      '找回密码',
      { confirmButtonText: '确认发送', cancelButtonText: '取消', type: 'warning' }
    )

    await authApi.forgotPassword(inputUser.trim())
    ElMessage.success(`临时密码已发送至 ${smtpInfo.email}`)
  } catch {
    // 用户取消
  } finally {
    forgotLoading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 380px;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
h2 {
  text-align: center;
  color: #303133;
  margin-bottom: 8px;
}
.subtitle {
  text-align: center;
  color: #909399;
  margin-bottom: 32px;
  font-size: 14px;
}
</style>
