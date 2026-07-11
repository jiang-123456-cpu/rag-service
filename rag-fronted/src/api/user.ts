// src/api/user.ts
import request from './request'
export interface LoginParams {
  username: string
  password: string
}

interface RegisterParams {
  username: string
  password: string,
  email: string
}

export const RGS = (data: RegisterParams) => {
  const { username, password, email } = data
  return request(
    {
      url: '/api/users/register',
      method: 'POST',
      data: {
        username,
        password,
        email
      }
    }
  )
}
export const LG = (data: LoginParams) => {
  const { username, password } = data
  return request(
    {
      url: '/api/users/login',
      method: 'POST',
      data: {
        username,
        password
      }
    }
  )
}
export const getUserList = () => {
  return request(
    {
      url: '/api/users',
      method: 'GET'
    }
  )
}
export const banUser = (id: number) => {
  return request(
    {
      url: '/api/users/disabled',
      method: 'POST',
      data: { id }
    }
  )
}
export const unbanUser = (id: number) => {
  return request(
    {
      url: '/api/users/unban',
      method: 'POST',
      data: { id }
    }
  )
}

