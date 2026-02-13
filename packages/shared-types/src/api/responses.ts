// Standard API response envelope
export interface ApiResponse<T> {
  data: T
  meta?: ResponseMeta
}

export interface ResponseMeta {
  cursor?: string
  hasMore?: boolean
  total?: number
}

// Error response
export interface ApiError {
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

// List responses
export interface PaginatedResponse<T> {
  data: T[]
  meta: {
    cursor?: string
    hasMore: boolean
    total?: number
  }
}
