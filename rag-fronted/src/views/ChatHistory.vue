<!-- src/views/ChatHistory.vue -->
<template>
  <div class="chat-history">
    <div class="search-bar">
      <el-select v-model="selectedKB" placeholder="按知识库筛选" clearable style="width: 300px" @change="handleKBChange">
        <el-option 
          v-for="item in knowledgeList" 
          :key="item.id" 
          :label="item.name" 
          :value="item.id" 
        />
      </el-select>
    </div>

    <el-card class="table-card">
      <el-table :data="chatList" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="question" label="问题" min-width="250" show-overflow-tooltip />
        <el-table-column prop="answer" label="回答" min-width="350" show-overflow-tooltip />
        <el-table-column prop="knowledgeBase" label="知识库" width="150" />
        <el-table-column prop="asker" label="提问者" width="120" />
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <div class="total-count">共 {{ total }} 条</div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="sizes, prev, pager, next, jumper"
          @current-change="loadChatList"
          @size-change="loadChatList"
        />
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="对话详情" width="700px" destroy-on-close>
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-item">
          <div class="detail-label">问题：</div>
          <div class="detail-value">{{ currentDetail.question }}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">回答：</div>
          <div class="detail-value answer-text">{{ currentDetail.answer }}</div>
        </div>
        <div class="detail-item" v-if="currentDetail.sources && currentDetail.sources.length > 0">
          <div class="detail-label">参考来源：</div>
          <div class="detail-value">
            <el-tag 
              v-for="(source, idx) in currentDetail.sources" 
              :key="idx" 
              size="small" 
              type="info" 
              style="margin-right: 8px; margin-bottom: 4px;"
            >
              {{ source.file_path || source.file_name || source }}
            </el-tag>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <div class="detail-label">知识库：</div>
            <div class="detail-value">{{ currentDetail.knowledgeBase }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">提问者：</div>
            <div class="detail-value">{{ currentDetail.asker }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">时间：</div>
            <div class="detail-value">{{ currentDetail.time }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getKnowledgebaseList } from '@/api/knowledgebase'
import { getChatList } from '@/api/chat'

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const selectedKB = ref<number | null>(null)
const loading = ref(false)
const detailVisible = ref(false)
const currentDetail = ref<any>(null)

const knowledgeList = ref<any[]>([])
const chatList = ref<any[]>([])

// 加载知识库列表
const loadKnowledgeList = async () => {
  try {
    const res = await getKnowledgebaseList()
    const items = res.data.items || res.data.data || []
    knowledgeList.value = items.map((item: any) => ({
      id: item.id,
      name: item.name
    }))
  } catch (e) {
    console.error('加载知识库列表失败', e)
  }
}

// 加载对话历史
const loadChatList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (selectedKB.value) {
      params.kb_id = selectedKB.value
    }
    const res = await getChatList(params)
    const data = res.data.data || res.data
    const items = data.items || []
    total.value = data.total || items.length

    chatList.value = items.map((item: any) => ({
      id: item.id,
      question: item.question || '',
      answer: item.answer || '',
      knowledgeBase: item.knowledge_base || item.knowledgeBase || item.kb_name || '',
      asker: item.questioner || item.asker || item.user || '系统管理员',
      time: item.create_time || item.createTime || item.time || '',
      sources: item.sources || item.references || []
    }))
  } catch (e) {
    ElMessage.error('加载对话历史失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleKBChange = () => {
  currentPage.value = 1
  loadChatList()
}

const showDetail = (row: any) => {
  currentDetail.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadKnowledgeList()
  loadChatList()
})
</script>

<style scoped lang="scss">
.chat-history {
  .search-bar {
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

  .detail-content {
    .detail-item {
      margin-bottom: 20px;

      .detail-label {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 8px;
      }

      .detail-value {
        font-size: 14px;
        color: #606266;
        line-height: 1.6;
        padding: 12px;
        background-color: #f5f7fa;
        border-radius: 4px;
        white-space: pre-wrap;
        word-break: break-word;

        &.answer-text {
          max-height: 300px;
          overflow-y: auto;
        }
      }
    }

    .detail-row {
      display: flex;
      gap: 20px;

      .detail-item {
        flex: 1;

        .detail-value {
          padding: 8px 12px;
        }
      }
    }
  }
}
</style>
