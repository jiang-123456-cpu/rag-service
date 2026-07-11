<!-- src/views/UserManage.vue -->
<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>用户管理</span>
      </div>
    </template>
    <el-table :data="userList" border>
      <el-table-column prop="id" label="ID" width="80">
        <template #default="{ row }">
          <span :class="{ 'banned-text': row.status === 'banned' }">{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名">
        <template #default="{ row }">
          <span :class="{ 'banned-text': row.status === 'banned' }">{{ row.username }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="role" label="角色">
        <template #default="{ row }">
          <span :class="{ 'banned-text': row.status === 'banned' }">{{ row.role }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱">
        <template #default="{ row }">
          <span :class="{ 'banned-text': row.status === 'banned' }">{{ row.email }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleUnban(row)">解禁</el-button>
          <el-button link type="danger" @click="handleBan(row)">禁用</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUserList, banUser, unbanUser } from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

interface UserInfo {
  id: number
  username: string
  role: string
  email: string
  status: 'normal' | 'banned'
}

const userList = ref<UserInfo[]>([])

onMounted(async () => {
  const res = await getUserList()
  console.log(res)
  userList.value = res.data.items
})

// 解禁用户
const handleUnban = (user: UserInfo) => {
  const id = user.id
  ElMessageBox.confirm(
    `确定解禁该用户 "${user.username}" 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    // 调用解禁接口
    unbanUser(id).then(() => {
      // 更新用户状态
      const index = userList.value.findIndex(item => item.id === id)
      if (index > -1) {
        userList.value[index].status = 'normal'
      }
      ElMessage.success(`用户 "${user.username}" 已解禁`)
    }).catch(() => {
      ElMessage.error('解禁失败')
    })
  }).catch(() => {
    // 用户点击取消
  })
}

// 禁用用户
const handleBan = (user: UserInfo) => {
  const id = user.id
  ElMessageBox.confirm(
    `确定禁用该用户 "${user.username}" 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    // 调用禁用接口
    banUser(id).then(() => {
      // 更新用户状态
      const index = userList.value.findIndex(item => item.id === id)
      if (index > -1) {
        userList.value[index].status = 'banned'
      }
      ElMessage.success(`用户 "${user.username}" 已禁用`)
    }).catch(() => {
      ElMessage.error('禁用失败')
    })
  }).catch(() => {
    // 用户点击取消
  })
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.banned-text {
  text-decoration: line-through;
  color: #999;
}
</style>