// src/stores/user.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { LG as loginApi } from '@/api/user.ts'
import type { LoginParams } from '@/api/user.ts'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const username = ref<string>(localStorage.getItem('username') || '')
  const role = ref<string>(localStorage.getItem('role') || 'admin')

  const isLoggedIn = ref(!!token.value)

  const login = async (params: LoginParams) => {
    try {
      const res = await loginApi(params)
      console.log(res)
      if (res.data.message === '登录成功') {
        const { token } = res.data
        localStorage.setItem('token', token)

        isLoggedIn.value = true
        return { success: true, message: '登录成功' }
      } else {
        return { success: false, message: res.data.message || '登录失败' }
      }
    } catch (error: any) {
      return { success: false, message: error.message || '请求失败' }
    }
  }

  const logout = () => {
    token.value = ''
    username.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
    isLoggedIn.value = false
  }

  return { token, username, role, isLoggedIn, login, logout }
})