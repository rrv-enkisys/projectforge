import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { auth } from './firebase'

// Create axios instance
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  headers: {
    'Content-Type': 'application/json',
  },
})

// DEVELOPMENT MODE: Skip Firebase auth
const DEV_MODE = import.meta.env.DEV || import.meta.env.MODE === 'development'

// Request interceptor to add Bearer token
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Let browser set Content-Type with boundary for multipart uploads
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // Skip auth in development mode
    if (DEV_MODE) {
      return config
    }

    const user = auth.currentUser
    if (user) {
      const token = await user.getIdToken()
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, sign out user
      await auth.signOut()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
