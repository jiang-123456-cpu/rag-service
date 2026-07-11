<!-- src/views/KnowledgeManage.vue -->
<template>
  <div class="knowledge-manage">
    <div class="search-bar">
      <el-input v-model="searchKeyword" placeholder="搜索知识库名称" clearable style="width: 300px" />
      <el-button type="primary" @click="handleAddKnowledge">
        <el-icon><Plus /></el-icon>
        新增知识库
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table :data="knowledgeList" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="知识库名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="300" />
        <el-table-column prop="docCount" label="文档数" width="100" />
        <el-table-column prop="creator" label="创建者" width="120" />
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <div class="total-count">共 {{ knowledgeList.length }} 条</div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="knowledgeList.length"
          layout="sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 新增/编辑知识库弹框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑知识库' : '新增知识库'" width="500px">
      <el-form :model="knowledgeForm" label-width="80px">
        <el-form-item label="知识库名称">
          <el-input v-model="knowledgeForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="knowledgeForm.description" type="textarea" :rows="4" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKnowledge">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getKnowledgebaseList, updateManager, deleteKnowledgebase, createKnowledgebase } from '@/api/knowledgebase'


const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const isEdit = ref(false)
const knowledgeForm = ref({
  id: 0,
  name: '',
  description: '',
  docCount: 0,
  creator: '系统管理员',
  createTime: new Date().toLocaleString()
})
// 组件卸载标志

interface Knowledgebase {
  id: number
  name: string
  description: string
  docCount: number
  creator: string
  createTime: string
}
const knowledgeList= ref<Knowledgebase[]>([])


onMounted(() => {
  getKnowledgebaseList().then(res => {
    console.log('API响应数据:', res.data.items)
    if (res.status === 200) {
      // 处理后端返回的数据，确保字段名匹配
      knowledgeList.value = res.data.items.map((item: any) => ({
        id: item.id,
        name: item.name,
        description: item.description,
        docCount: item.document_count,
        creator: item.creator || item.created_by || item.author || '系统管理员',
        createTime: item.createTime || item.created_at || item.create_time || new Date().toLocaleString()
      }))
    }
  }).catch((error) => {
    console.error('加载知识库列表失败:', error)
    // 如果API请求失败，使用mock数据
    knowledgeList.value = [
      { id: 1, name: '产品帮助中心', description: '产品使用帮助文档', docCount: 15, creator: '系统管理员', createTime: '2024-01-15 10:30:00' },
      { id: 2, name: '公司规章制度', description: '公司内部规章制度', docCount: 8, creator: '系统管理员', createTime: '2024-01-16 14:20:00' },
      { id: 3, name: '技术文档库', description: '技术开发文档', docCount: 23, creator: '系统管理员', createTime: '2024-01-17 09:15:00' }
    ]
  })
})


const handleAddKnowledge = () => {
  isEdit.value = false
 
  dialogVisible.value = true
}

const handleEdit = (row: Knowledgebase) => {
  isEdit.value = true
  knowledgeForm.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = (row: Knowledgebase) => {    
  ElMessageBox.confirm('确定要删除该知识库吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    deleteKnowledgebase(row.id).then(res => {
      if (res.data.message === 'Knowledge base deleted successfully') {
        ElMessage.success('删除成功')
        const index = knowledgeList.value.findIndex((item: Knowledgebase) => item.id === row.id)
        if (index > -1) {
          knowledgeList.value.splice(index, 1)
        }
      }
    }).catch(() => {
      
        ElMessage.error('删除失败')
      
    })
  }).catch(() => {})
}

const handleSaveKnowledge = () => {
  if (isEdit.value) {
      // 编辑模式
    const updateData = {
      name: knowledgeForm.value.name,
      description: knowledgeForm.value.description
    }
    updateManager(knowledgeForm.value.id, updateData).then(res => {
      if (res.data.message === 'Knowledge base updated successfully') {
        ElMessage.success('更新成功')
        // 更新列表中的数据，保留原有字段
        const index = knowledgeList.value.findIndex((item: any) => item.id === knowledgeForm.value.id)
        if (index > -1) {
          knowledgeList.value[index] = { 
            ...knowledgeList.value[index],
            name: knowledgeForm.value.name,
            description: knowledgeForm.value.description
          }
        }
        dialogVisible.value = false
      }
    }).catch(() => {
      ElMessage.error('更新失败')
    })
  } else {
    // 新增模式
    createKnowledgebase(knowledgeForm.value).then(res => {
      if (res.data.message === 'Knowledge base created successfully') {
        ElMessage.success('新增成功')
        // 将新创建的知识库添加到列表
        let obj={
          id:res.data.id,
          name:knowledgeForm.value.name,
          description:knowledgeForm.value.description,
          docCount:0,
          creator:'系统管理员',
          createTime:new Date().toLocaleString()
        }
        knowledgeList.value.push(obj as Knowledgebase)
        dialogVisible.value = false
      }
    }).catch(() => {
      
        ElMessage.error('新增失败')
      
    })
  }
}
</script>

<style scoped lang="scss">
.knowledge-manage {
  .search-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .table-card {
    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 16px 20px;
    border-top: 1px solid #ebeef5;

    .total-count {
      margin-right: auto;
      color: #909399;
      font-size: 14px;
    }
  }
}
</style>
