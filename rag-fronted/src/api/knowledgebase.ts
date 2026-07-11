import request from './request'

interface KnowledgebaseParams {
  name: string
  description: string
}

export const createKnowledgebase = (data: KnowledgebaseParams) => {
  const { name, description } = data
  return request(
    {
      url: '/api/knowledgebase/create',
      method: 'POST',
      data: {
        name,
        description
      }
    }
  )
}

export const getKnowledgebaseList = () => {
  return request(
    {
      url: '/api/knowledgebase/',
      method: 'GET'
    }
  )
}
export const updateManager = (id: number, data: KnowledgebaseParams) => {
  const { name, description } = data
  return request(
    {
      url: `/api/knowledgebase/update`,
      method: 'POST',
      data: {
        name,
        description,
        id
      }
    }
  )
}
export const deleteKnowledgebase = (id: number) => {
  return request(
    {
      url: `/api/knowledgebase/delete`,
      method: 'POST',
      data: { id }
    }
  )
}
