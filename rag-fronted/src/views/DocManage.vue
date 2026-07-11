<!-- src/views/DocManage.vue -->
<template>
  <div class="doc-manage">
    <div class="search-bar">
      <el-select v-model="selectedKnowledge" placeholder="选择知识库筛选" clearable style="width: 300px" @change="handleKnowledgeChange">
        <el-option 
          v-for="item in knowledgeList" 
          :key="item.id" 
          :label="item.name" 
          :value="item.id" 
        />
      </el-select>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传文档
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table :data="filteredDocList" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="文件名" min-width="250" />
        <el-table-column prop="knowledgeName" label="所属知识库" width="150" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getTagType(row.type)">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="100" />
        <el-table-column prop="chunkCount" label="分块数" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="success">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploadTime" label="上传时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <div class="total-count">共 {{ filteredDocList.length }} 条</div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredDocList.length"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 上传文档弹框 -->
    <UploadDocumentDialog 
      v-model="showUploadDialog" 
      @success="handleUploadSuccess" 
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import UploadDocumentDialog from '@/components/UploadDocumentDialog.vue'
import { getDocumentList, deleteDocument } from '@/api/document'
import { getKnowledgebaseList } from '@/api/knowledgebase'
import type { DocumentItem } from '@/api/document'

const selectedKnowledge = ref<number | ''>('')
const currentPage = ref(1)
const pageSize = ref(10)
const showUploadDialog = ref(false)
const loading = ref(false)

const knowledgeList = ref<{ id: number; name: string }[]>([])
const docList = ref<DocumentItem[]>([])

const filteredDocList = computed(() => {
  if (!selectedKnowledge.value) return docList.value
  const kbName = knowledgeList.value.find(kb => kb.id === selectedKnowledge.value)?.name
  if (!kbName) return docList.value
  return docList.value.filter(item => item.knowledgeName === kbName)
})

const getTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'MD': 'primary',
    'DOCX': 'success',
    'PDF': 'info',
    'TXT': 'warning'
  }
  return typeMap[type] || ''
}

const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': '处理中',
    'ready': '已就绪',
    'failed': '失败',
    'processing': '处理中',
    'completed': '已完成',
    'uploading': '上传中'
  }
  return statusMap[status] || status || '未知'
}

const loadKnowledgeList = () => {
  getKnowledgebaseList().then(res => {
    if (res.status === 200) {
      knowledgeList.value = res.data.items.map((item: any) => ({
        id: item.id,
        name: item.name
      }))
    }
  }).catch(() => {
    knowledgeList.value = [
      { id: 1, name: '公司规章制度' },
      { id: 2, name: '技术文档库' },
      { id: 3, name: '产品帮助中心' }
    ]
  })
}

const loadDocumentList = () => {
  loading.value = true
  // 不传 kbId，获取所有文档，由前端做筛选
  getDocumentList().then(res => {
    if (res.status === 200) {
      console.log('后端文档数据:', res.data.items)
      docList.value = res.data.items.map((item: any) => {
        // 优先使用 kb_id，如果没有则通过 knowledge_name 查找
        let kbId = item.kb_id || item.knowledgeId || item.knowledge_id || 0
        if (!kbId && item.knowledge_name) {
          const kb = knowledgeList.value.find(k => k.name === item.knowledge_name)
          if (kb) kbId = kb.id
        }
        return {
          id: item.id,
          name: item.name || item.filename || item.file_name || '未知文件名',
          knowledgeId: kbId,
          knowledgeName: item.knowledge_name || item.knowledgeName || item.kb_name || '',
          type: item.type || item.file_type || item.extension || '',
          size: item.size || item.file_size || '',
          chunkCount: item.chunk_count || item.chunkCount || item.chunks || 0,
          status: getStatusText(item.status),
          uploadTime: item.upload_time || item.uploadTime || item.created_at || new Date().toLocaleString()
        }
      })
    }
    loading.value = false
  }).catch(() => {
    loading.value = false
    docList.value = [
      { id: 14, name: '员工请假管理办法.md', knowledgeId: 1, knowledgeName: '公司规章制度', type: 'MD', size: '3.2 KB', chunkCount: 4, status: '已就绪', uploadTime: '2026-03-21 19:47:12' },
      { id: 15, name: '员工行为规范手册.docx', knowledgeId: 1, knowledgeName: '公司规章制度', type: 'DOCX', size: '37.6 KB', chunkCount: 3, status: '已就绪', uploadTime: '2026-03-21 19:47:39' },
      { id: 16, name: 'API接口设计规范.md', knowledgeId: 2, knowledgeName: '技术文档库', type: 'MD', size: '3.6 KB', chunkCount: 6, status: '已就绪', uploadTime: '2026-03-21 19:48:11' },
      { id: 17, name: 'Git版本管理规范.docx', knowledgeId: 2, knowledgeName: '技术文档库', type: 'DOCX', size: '37.5 KB', chunkCount: 3, status: '已就绪', uploadTime: '2026-03-21 19:48:46' },
      { id: 18, name: 'Python开发编码规范.txt', knowledgeId: 2, knowledgeName: '技术文档库', type: 'TXT', size: '3.1 KB', chunkCount: 4, status: '已就绪', uploadTime: '2026-03-21 19:49:09' },
      { id: 19, name: '数据库设计规范.pdf', knowledgeId: 2, knowledgeName: '技术文档库', type: 'PDF', size: '43.2 KB', chunkCount: 3, status: '已就绪', uploadTime: '2026-03-21 19:49:34' },
      { id: 20, name: '企业OA系统使用手册.txt', knowledgeId: 3, knowledgeName: '产品帮助中心', type: 'TXT', size: '3.7 KB', chunkCount: 4, status: '已就绪', uploadTime: '2026-03-21 19:50:13' },
      { id: 21, name: '企业邮箱配置说明.pdf', knowledgeId: 3, knowledgeName: '产品帮助中心', type: 'PDF', size: '42.3 KB', chunkCount: 3, status: '已就绪', uploadTime: '2026-03-21 19:50:41' },
      { id: 22, name: '项目管理平台操作指南.md', knowledgeId: 3, knowledgeName: '产品帮助中心', type: 'MD', size: '4.1 KB', chunkCount: 5, status: '已就绪', uploadTime: '2026-03-21 19:51:05' },
      { id: 23, name: '新员工入职指南.docx', knowledgeId: 3, knowledgeName: '产品帮助中心', type: 'DOCX', size: '37.7 KB', chunkCount: 3, status: '已就绪', uploadTime: '2026-03-21 19:51:34' }
    ]
  })
}

const handleDelete = (row: DocumentItem) => {
  ElMessageBox.confirm('确定要删除该文档吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    deleteDocument(row.id).then(res => {
      if (res.data.message === '删除成功') {
        ElMessage.success('删除成功')
        const index = docList.value.findIndex(item => item.id === row.id)
        if (index > -1) {
          docList.value.splice(index, 1)
        }
      }
    }).catch(() => {
      ElMessage.error('删除失败')
    })
  }).catch(() => {})
}

const handleUploadSuccess = (doc: DocumentItem) => {
  docList.value.unshift(doc)
}

const handleKnowledgeChange = () => {
  currentPage.value = 1
  loadDocumentList()
}

onMounted(async () => {
  await loadKnowledgeList()
  await loadDocumentList()
})
</script>

<style scoped lang="scss">
.doc-manage {
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