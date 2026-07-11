<!-- src/views/IntelligentQA.vue -->
<template>
  <div class="intelligent-qa">
    <div class="qa-container">
      <!-- 左侧知识库列表 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <span class="sidebar-title">选择知识库</span>
        </div>
        <div class="knowledge-list">
          <div 
            v-for="item in knowledgeList" 
            :key="item.id"
            class="knowledge-item"
            :class="{ active: selectedKnowledge === item.id }"
            @click="selectKnowledge(item.id)"
          >
            <el-icon><Folder /></el-icon>
            <span>{{ item.name }}</span>
            <el-tag size="small" type="info">{{ item.docCount }}篇</el-tag>
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-area">
        <div v-if="!selectedKnowledge" class="empty-state">
          <el-icon :size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
          <div class="empty-title">欢迎使用企业知识库问答系统</div>
          <div class="empty-desc">请从左侧选择知识库，然后输入您的问题</div>
        </div>

        <div v-else class="chat-content">
          <!-- 消息列表 -->
          <div class="messages-container" ref="messagesContainer">
            <div v-if="messages.length === 0" class="welcome-message">
              <div class="welcome-avatar">
                <el-icon :size="32" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <div class="welcome-text">
                <div class="welcome-title">您好！我是企业知识库助手</div>
                <div class="welcome-desc">我可以帮您解答关于企业OA、规章制度、技术文档等问题。请问有什么可以帮您？</div>
                <div class="welcome-time">{{ currentTime }}</div>
              </div>
            </div>

            <div v-for="msg in messages" :key="msg.id" class="message-item" :class="msg.type">
              <div v-if="msg.type === 'assistant'" class="message-avatar">
                <el-icon :size="24" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <div class="message-bubble">
                <div class="message-content">{{ msg.content }}</div>
                <div v-if="msg.references && msg.references.length > 0" class="message-references">
                  <div class="references-label">参考来源：</div>
                  <div class="references-list">
                    <el-tag v-for="(ref, idx) in msg.references" :key="idx" size="small" type="info" style="margin-right: 8px; margin-bottom: 4px;">
                      {{ ref }}
                    </el-tag>
                  </div>
                </div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
              <div v-if="msg.type === 'user'" class="message-avatar">
                <el-icon :size="24" color="#67c23a"><User /></el-icon>
              </div>
            </div>

            <!-- 打字机效果：正在输出中的AI消息 -->
            <div v-if="streamingMessage" class="message-item assistant">
              <div class="message-avatar">
                <el-icon :size="24" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <div class="message-bubble">
                <div class="message-content">{{ streamingContent }}</div>
                <span class="typing-cursor">|</span>
              </div>
            </div>

            <!-- 加载中 -->
            <div v-if="isLoading && !streamingMessage" class="message-item assistant">
              <div class="message-avatar">
                <el-icon :size="24" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <div class="message-bubble">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-area">
            <div class="input-wrapper">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题..."
                @keydown.enter.ctrl="handleSend"
                resize="none"
              />
            </div>
            <div class="action-bar">
              <span class="input-tip">Ctrl + Enter 发送</span>
              <el-button type="primary" @click="handleSend" :loading="isLoading" :disabled="!inputText.trim()">
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { Folder, ChatDotRound, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getKnowledgebaseList } from '@/api/knowledgebase'
import { askChat } from '@/api/chat'

const messagesContainer = ref<HTMLElement>()
const selectedKnowledge = ref<number | null>(null)
const inputText = ref('')
const isLoading = ref(false)
const messages = ref<any[]>([])
const streamingMessage = ref(false)
const streamingContent = ref('')
const sessionId = ref('')

const knowledgeList = ref<any[]>([])

const currentTime = ref('')

// 加载知识库列表
const loadKnowledgeList = async () => {
  try {
    const res = await getKnowledgebaseList()
    const items = res.data.items || res.data.data || []
    knowledgeList.value = items.map((item: any) => ({
      id: item.id,
      name: item.name,
      docCount: item.doc_count || item.docCount || item.document_count || 0
    }))
  } catch (e) {
    console.error('加载知识库列表失败', e)
  }
}

const selectKnowledge = (id: number) => {
  selectedKnowledge.value = id
  messages.value = []
  sessionId.value = ''
}

const handleSend = async () => {
  if (!inputText.value.trim() || isLoading.value || !selectedKnowledge.value) return

  const userContent = inputText.value.trim()
  const now = new Date()
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    type: 'user',
    content: userContent,
    time: timeStr
  })

  inputText.value = ''
  isLoading.value = true
  streamingMessage.value = false
  streamingContent.value = ''
  scrollToBottom()

  try {
    const res = await askChat({
      question: userContent,
      kb_id: selectedKnowledge.value,
      session_id: sessionId.value
    })

    const data = res.data.data || res.data
    const answer = data.answer || data.message || '暂无回答'
    const sources = data.sources || data.references || []
    const newSessionId = data.session_id || sessionId.value
    sessionId.value = newSessionId

    // 打字机效果
    streamingMessage.value = true
    streamingContent.value = ''
    scrollToBottom()

    let charIndex = 0
    const typingSpeed = 30 // 每个字符的间隔毫秒

    const typeNextChar = () => {
      if (charIndex < answer.length) {
        streamingContent.value += answer[charIndex]
        charIndex++
        scrollToBottom()
        setTimeout(typeNextChar, typingSpeed)
      } else {
        // 打字完成，将消息加入列表
        const refs = sources.map((s: any) => {
          const name = s.file_path || s.file_name || s.fileName || s.name || ''
          // 提取文件名
          const parts = name.split('/')
          return parts[parts.length - 1] || name
        })

        messages.value.push({
          id: Date.now(),
          type: 'assistant',
          content: answer,
          references: refs,
          time: timeStr
        })
        streamingMessage.value = false
        streamingContent.value = ''
        isLoading.value = false
        scrollToBottom()
      }
    }

    typeNextChar()
  } catch (e) {
    ElMessage.error('请求失败，请稍后重试')
    isLoading.value = false
    streamingMessage.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  const now = new Date()
  currentTime.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  loadKnowledgeList()
})
</script>

<style scoped lang="scss">
.intelligent-qa {
  height: 100%;
  padding: 0;
  margin: 0;

  .qa-container {
    display: flex;
    height: calc(100vh - 140px);
    background-color: #fff;
    border-radius: 4px;
    overflow: hidden;
  }

  .sidebar {
    width: 280px;
    border-right: 1px solid #e4e7ed;
    display: flex;
    flex-direction: column;

    .sidebar-header {
      padding: 16px 20px;
      border-bottom: 1px solid #e4e7ed;
      background-color: #f5f7fa;

      .sidebar-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }
    }

    .knowledge-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;

      .knowledge-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          background-color: #f5f7fa;
        }

        &.active {
          background-color: #ecf5ff;
          color: #409eff;
        }

        span {
          flex: 1;
          font-size: 14px;
        }

        .el-tag {
          flex-shrink: 0;
        }
      }
    }
  }

  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;

    .empty-state {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: #909399;

      .empty-title {
        margin-top: 16px;
        font-size: 18px;
        font-weight: 600;
        color: #606266;
      }

      .empty-desc {
        margin-top: 8px;
        font-size: 14px;
      }
    }

    .chat-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100%;

      .messages-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background-color: #f5f7fa;

        .welcome-message {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;

          .welcome-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background-color: #e6f2ff;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
          }

          .welcome-text {
            background-color: #fff;
            padding: 16px 20px;
            border-radius: 12px;
            max-width: 70%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

            .welcome-title {
              font-size: 15px;
              font-weight: 600;
              color: #303133;
              margin-bottom: 8px;
            }

            .welcome-desc {
              font-size: 14px;
              color: #606266;
              line-height: 1.6;
              margin-bottom: 8px;
            }

            .welcome-time {
              font-size: 12px;
              color: #c0c4cc;
              text-align: right;
            }
          }
        }

        .message-item {
          display: flex;
          gap: 12px;
          margin-bottom: 20px;

          &.user {
            flex-direction: row-reverse;

            .message-bubble {
              background-color: #409eff;
              color: #fff;
            }
          }

          .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #e6f2ff;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
          }

          .message-bubble {
            background-color: #fff;
            padding: 14px 18px;
            border-radius: 12px;
            max-width: 65%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            position: relative;

            .message-content {
              font-size: 14px;
              line-height: 1.6;
              margin-bottom: 10px;
              white-space: pre-wrap;
              word-break: break-word;
            }

            .typing-cursor {
              display: inline-block;
              font-size: 16px;
              font-weight: bold;
              color: #409eff;
              animation: blink 0.8s infinite;
              margin-left: 2px;
            }

            .message-references {
              padding-top: 10px;
              border-top: 1px solid #ebeef5;

              .references-label {
                font-size: 12px;
                color: #909399;
                margin-bottom: 6px;
              }

              .references-list {
                display: flex;
                flex-wrap: wrap;
              }
            }

            .message-time {
              font-size: 12px;
              color: #c0c4cc;
              text-align: right;
              margin-top: 8px;
            }

            .typing-indicator {
              display: flex;
              gap: 4px;

              span {
                width: 8px;
                height: 8px;
                background-color: #909399;
                border-radius: 50%;
                animation: typing 1.4s infinite ease-in-out;

                &:nth-child(1) { animation-delay: 0s; }
                &:nth-child(2) { animation-delay: 0.2s; }
                &:nth-child(3) { animation-delay: 0.4s; }
              }
            }
          }
        }
      }

      .input-area {
        padding: 16px 20px;
        border-top: 1px solid #e4e7ed;
        background-color: #fff;

        .input-wrapper {
          margin-bottom: 12px;
        }

        .action-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .input-tip {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
