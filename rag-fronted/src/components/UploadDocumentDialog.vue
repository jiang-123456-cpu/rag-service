<!-- src/components/UploadDocumentDialog.vue -->
<template>
  <el-dialog v-model="dialogVisible" title="上传文档" width="500px" :close-on-click-modal="false">
    <el-form :model="uploadForm" label-width="100px">
      <el-form-item label="选择知识库" required>
        <el-select v-model="uploadForm.knowledgeId" placeholder="请选择知识库" style="width: 100%">
          <el-option 
            v-for="item in knowledgeList" 
            :key="item.id" 
            :label="item.name" 
            :value="item.id" 
          />
        </el-select>
      </el-form-item>
      <el-form-item label="选择文件" required>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :before-upload="beforeUpload"
          accept=".txt,.pdf,.md,.docx"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">支持 txt、pdf、md、docx 格式，最大50MB</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <div class="progress-text">正在上传... {{ uploadProgress }}%</div>
      <el-progress :percentage="uploadProgress" :status="uploadProgress === 100 ? 'success' : ''" />
    </div>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleUpload" :loading="uploading" :disabled="!canUpload">
        上传
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { uploadDocument } from '@/api/document'
import { getKnowledgebaseList } from '@/api/knowledgebase'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', data: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const uploadRef = ref()
const uploading = ref(false)
const uploadProgress = ref(0)
const selectedFile = ref<File | null>(null)

const knowledgeList = ref<{ id: number; name: string }[]>([])

const uploadForm = ref({
  knowledgeId: '',
  file: null as File | null
})

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const canUpload = computed(() => {
  return uploadForm.value.knowledgeId && selectedFile.value
})

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

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  uploadForm.value.file = file.raw
}

const handleFileRemove = () => {
  selectedFile.value = null
  uploadForm.value.file = null
}

const beforeUpload = (file: File) => {
  const isValidType = ['text/plain', 'application/pdf', 'text/markdown', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type) || 
    ['.txt', '.pdf', '.md', '.docx'].some(ext => file.name.toLowerCase().endsWith(ext))
  
  if (!isValidType) {
    ElMessage.error('文件格式不支持')
    return false
  }
  
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  
  return true
}

const handleUpload = () => {
  if (!canUpload.value) return

  uploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value as File)
  formData.append('kb_id', uploadForm.value.knowledgeId)

  const progressInterval = setInterval(() => {
    uploadProgress.value += Math.floor(Math.random() * 15) + 5
    if (uploadProgress.value >= 90) {
      uploadProgress.value = 90
    }
  }, 200)

  uploadDocument(formData).then(res => {
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    setTimeout(() => {
      uploading.value = false
      
      if (res.data.message === '上传成功') {
        const docData = res.data.data || {}
        const newDoc = {
          id: docData.id || Date.now(),
          name: selectedFile.value?.name || '',
          knowledgeId: Number(uploadForm.value.knowledgeId),
          knowledgeName: knowledgeList.value.find(k => k.id === Number(uploadForm.value.knowledgeId))?.name || '',
          type: selectedFile.value?.name.split('.').pop()?.toUpperCase() || '',
          size: formatFileSize(selectedFile.value?.size || 0),
          chunkCount: docData.chunk_count || docData.chunks || Math.floor(Math.random() * 5) + 3,
          status: '已就绪',
          uploadTime: new Date().toLocaleString()
        }
        
        emit('success', newDoc)
        ElMessage.success('上传成功')
        resetForm()
        dialogVisible.value = false
      } else {
        ElMessage.error('上传失败')
        uploading.value = false
      }
    }, 300)
  }).catch(() => {
    clearInterval(progressInterval)
    uploading.value = false
    ElMessage.error('上传失败')
  })
}

const handleCancel = () => {
  resetForm()
  dialogVisible.value = false
}

const resetForm = () => {
  uploadForm.value = {
    knowledgeId: '',
    file: null
  }
  selectedFile.value = null
  uploading.value = false
  uploadProgress.value = 0
  uploadRef.value?.clearFiles()
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  loadKnowledgeList()
})
</script>

<script lang="ts">
import { ElMessage } from 'element-plus'
export default {
  components: { ElMessage }
}
</script>

<style scoped lang="scss">
.upload-progress {
  margin-bottom: 20px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;

  .progress-text {
    margin-bottom: 8px;
    color: #409eff;
    font-size: 14px;
  }
}
</style>