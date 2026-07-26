<template>
  <div class="page-container">
    <h3 style="margin-bottom:20px">修改账户名</h3>
    <p style="color:#909399;font-size:13px;margin-bottom:12px">当前账户名：<strong>{{ currentUsername }}</strong></p>
    <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="120px" style="max-width:400px">
      <el-form-item label="新用户名" prop="username">
        <el-input v-model="userForm.username" placeholder="输入新用户名" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleChangeUsername" :loading="changingUser">修改用户名</el-button>
      </el-form-item>
    </el-form>

    <el-divider />

    <h3 style="margin-bottom:20px">修改密码</h3>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { authApi } from '../../api'
import { useAuthStore } from '../../stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const currentUsername = ref(authStore.username)

const pwdFormRef = ref()
const userFormRef = ref()
const changingPwd = ref(false)
const changingUser = ref(false)

const userForm = reactive({ username: '' })

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

const userRules = {
  username: [{ required: true, message: '请输入新用户名', trigger: 'blur' }]
}

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ]
}

async function handleChangeUsername() {
  const valid = await userFormRef.value?.validate().catch(() => false)
  if (!valid) return
  changingUser.value = true
  try {
    const res = await authApi.changeUsername(userForm.username)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('username', res.data.username)
    authStore.$patch({ username: res.data.username, token: res.data.token })
    currentUsername.value = res.data.username
    ElMessage.success('用户名修改成功')
    userForm.username = ''
  } finally { changingUser.value = false }
}

async function handleChangePwd() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  changingPwd.value = true
  try {
    await authApi.changePassword(pwdForm.oldPassword, pwdForm.newPassword)
    ElMessage.success('密码修改成功')
    pwdForm.oldPassword = ''; pwdForm.newPassword = ''; pwdForm.confirmPassword = ''
  } finally { changingPwd.value = false }
}
</script>
