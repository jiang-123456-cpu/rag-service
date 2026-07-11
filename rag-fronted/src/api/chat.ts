import request from './request'

// 提问
export const askChat = (data: { question: string; kb_id: number; session_id?: string }) => {
  return request({
    url: '/api/chat/ask',
    method: 'POST',
    data
  })
}

// 获取对话历史列表
export const getChatList = (params?: { page?: number; page_size?: number; kb_id?: number }) => {
  return request({
    url: '/api/chat/list',
    method: 'GET',
    params
  })
}
