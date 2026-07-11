<!-- src/layouts/MainLayout.vue -->
<template>
  <div class="main-layout">
    <div class="sidebar">
      <div class="logo-area">
        <h2>企业知识库</h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#1890ff"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>数据概览</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Document /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><Folder /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/qa">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/chat-history">
          <el-icon><Clock /></el-icon>
          <span>对话历史</span>
        </el-menu-item>
      </el-menu>
    </div>
    
    <div class="main-content">
      <div class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span style="margin-left: 8px">{{ userStore.username || '系统管理员' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { UserFilled, ArrowDown, Clock, ChatDotRound, DataLine, Document, Folder, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title as string || '仪表板')

const handleMenuSelect = (index: string) => {
  router.push(index)
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  } else if (command === 'profile') {
    ElMessage.info('个人中心开发中')
  }
}
</script>

<style scoped lang="scss">
.main-layout {
  display: flex;
  height: 100%;
  width: 100%;
}

.sidebar {
  width: 260px;
  background-color: #001529;
  color: #fff;
  display: flex;
  flex-direction: column;
  
  .logo-area {
    padding: 20px;
    border-bottom: 1px solid #0d2c3e;
    
    h2 {
      color: #fff;
      font-size: 20px;
      margin: 0;
      text-align: center;
    }
  }
  
  .sidebar-menu {
    flex: 1;
    border-right: none;
    background-color: #001529;
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
  
  .header {
    height: 60px;
    background: #fff;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    z-index: 10;
    
    .header-right {
      .user-info {
        display: flex;
        align-items: center;
        cursor: pointer;
        color: #333;
      }
    }
  }
  
  .content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
  }
}
</style>