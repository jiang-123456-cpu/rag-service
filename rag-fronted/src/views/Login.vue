<!-- src/views/Login.vue -->
<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>企业知识库问答系统</h2>
        <p>基于RAG的智能知识检索与问答平台</p>
      </div>

      <!-- 登录/注册标签切换 -->
      <div class="tabs-wrapper">
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          登录
        </div>
        <div 
          class="tab-item" 
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >
          注册
        </div>
      </div>

      <!-- 登录表单 -->
      <el-form 
        v-if="activeTab === 'login'" 
        :model="loginForm" 
        :rules="loginRules" 
        ref="loginFormRef" 
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <div class="form-actions">
          <el-button type="primary" size="large" :loading="loading" @click="handleLogin" style="width: 100%">
            登录
          </el-button>
        </div>
        <div class="login-footer">
          <el-link type="primary" @click="activeTab = 'register'" style="font-size: 14px;">
            还没有账号？马上注册
          </el-link>
        </div>
        <div class="login-tips">
          <el-text type="info" size="small">测试账号：admin/123456（管理员）| user1/123456（普通用户）</el-text>
        </div>
      </el-form>

      <!-- 注册表单 -->
      <el-form 
        v-if="activeTab === 'register'" 
        :model="registerForm" 
        :rules="registerRules" 
        ref="registerFormRef"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            type="email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <div class="form-actions">
          <el-button type="primary" size="large" :loading="loading" @click="handleRegister" style="width: 100%">
            注册
          </el-button>
        </div>
        <div class="login-footer">
          <el-link type="primary" @click="activeTab = 'login'" style="font-size: 14px;">
            已有账号？立即登录
          </el-link>
        </div>
      </el-form>

      <!-- 错误提示 -->
      <div v-if="errorMsg" class="error-msg">
        <el-alert :title="errorMsg" type="error" show-icon :closable="false" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { RGS } from '@/api/user'
const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref<FormInstance>()

const loading = ref(false)
const errorMsg = ref('')
const activeTab = ref<'login' | 'register'>('login')

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  password: ''
})

const registerRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      errorMsg.value = ''
      const result = await userStore.login(loginForm)
      loading.value = false
      if (result.success) {
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } else {
        errorMsg.value = result.message
      }
    }
  })
}

const handleRegister = async () => {
  const res = await RGS(registerForm)
  console.log(res)
  if (res.data.message === '注册成功') {
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    // 清空注册表单
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
  } else {
    errorMsg.value = res.data.message
  }
}
</script>

<style scoped lang="scss">
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('https://images.pexels.com/photos/531880/pexels-photo-531880.jpeg?auto=compress&cs=tinysrgb&w=1920&h=1080&dpr=2');
  background-size: cover;
  background-position: center;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
  }
}

.login-card {
  width: 450px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  
  h2 {
    font-size: 28px;
    color: #303133;
    margin-bottom: 8px;
  }
  
  p {
    color: #606266;
    font-size: 14px;
  }
}

.tabs-wrapper {
  display: flex;
  margin-bottom: 30px;
  border-bottom: 1px solid #e4e7ed;
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: 12px 0;
    font-size: 18px;
    font-weight: 500;
    color: #606266;
    cursor: pointer;
    position: relative;
    transition: color 0.2s;
    
    &:hover {
      color: #409eff;
    }
    
    &.active {
      color: #409eff;
      
      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 50%;
        transform: translateX(-50%);
        width: 40px;
        height: 2px;
        background-color: #409eff;
        border-radius: 2px;
      }
    }
  }
}

.form-actions {
  margin-top: 16px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
}

.login-tips {
  text-align: center;
  margin-top: 16px;
}

.error-msg {
  margin-top: 16px;
}
</style>