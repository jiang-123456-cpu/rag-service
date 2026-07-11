import request from './request'

export interface DocumentItem {
  id: number
  name: string
  knowledgeId: number
  knowledgeName: string
  type: string
  size: string
  chunkCount: number
  status: string
  uploadTime: string
}

export const getDocumentList = (kbId?: number) => {
  return request({
    url: '/api/document/list',
    method: 'GET',
    params: kbId ? { kb_id: kbId } : {}
  })
}

export const uploadDocument = (formData: FormData) => {
  return request({
    url: '/api/document/upload',
    method: 'POST',
    data: formData,

    // 不手动设置 Content-Type，让浏览器自动添加正确的 boundary
  })
}

export const deleteDocument = (docId: number) => {
  return request({
    url: '/api/document/delete',
    method: 'POST',
    params: { doc_id: docId }
  })
}