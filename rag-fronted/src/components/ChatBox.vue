<!-- src/components/ChatBox.vue -->
<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="msg in chatStore.messages" :key="msg.id" class="message-item" :class="msg.type">
        <div class="message-avatar">
          <el-avatar :size="32" v-if="msg.type === 'assistant'">
            <el-icon><Service /></el-icon>
          </el-avatar>
          <el-avatar :size="32" v-else>
            <el-icon><User /></el-icon>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-text">{{ msg.content }}</div>
          <div class="message-references" v-if="msg.references && msg.references.length">
            <div class="ref-title">参考来源：</div>
            <div class="ref-list">
              <el-link v-for="(ref, idx) in msg.references" :key="idx" type="info" :href="ref.url" target="_blank">
                {{ ref.fileName }}
              </el-link>
            </div>
          </div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      <div v-if="chatStore.isLoading" class="message-item assistant">
        <div class="message-avatar">
          <el-avatar :size="32">
            <el-icon><Service /></el-icon>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="请输入您的问题..."
        @keydown.ctrl.enter="sendMessage"
      />
      <div class="input-actions">
        <el-button type="primary" :loading="chatStore.isLoading" @click="sendMessage" :disabled="!inputText.trim()">
          发送
        </el-button>
        <span class="tip">Ctrl + Enter 发送</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { Service, User } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat.ts'

const chatStore = useChatStore()
const inputText = ref('')
const messagesContainer = ref<HTMLElement>()

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  await chatStore.sendMessage(text)
  scrollToBottom()
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

watch(() => chatStore.messages.length, () => {
  scrollToBottom()
}, { immediate: true })
</script>

<style scoped lang="scss">
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 500px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  
  &.user {
    flex-direction: row-reverse;
    
    .message-content {
      background: #1890ff;
      color: white;
      margin-right: 12px;
      margin-left: 0;
      
      .message-time {
        color: rgba(255,255,255,0.8);
      }
    }
  }
  
  &.assistant {
    .message-content {
      background: white;
      border: 1px solid #e9ecef;
    }
  }
  
  .message-avatar {
    flex-shrink: 0;
  }
  
  .message-content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    margin-left: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    
    .message-text {
      font-size: 14px;
      line-height: 1.5;
      word-break: break-word;
    }
    
    .message-references {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid #e9ecef;
      font-size: 12px;
      
      .ref-title {
        color: #666;
        margin-bottom: 4px;
      }
      
      .ref-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
    }
    
    .message-time {
      font-size: 11px;
      margin-top: 6px;
      text-align: right;
      color: #999;
    }
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
  
  span {
    width: 8px;
    height: 8px;
    background: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite;
    
    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

.chat-input {
  margin-top: 16px;
  
  .input-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    
    .tip {
      font-size: 12px;
      color: #999;
    }
  }
}
</style>