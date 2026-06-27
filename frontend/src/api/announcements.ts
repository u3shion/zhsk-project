const API_BASE = '/api'

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {}

  const isFormData = body instanceof FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json().catch(() => ({ detail: null }))

  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    throw new Error(
      typeof data?.detail === 'string' && data.detail
        ? data.detail
        : `Ошибка ${res.status}`,
    )
  }

  return data as T
}

export interface AnnouncementResponse {
  id: number
  author_id: number
  author_role: string
  type: string
  title: string
  content: string
  photo_urls: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AnnouncementsListResponse {
  items: AnnouncementResponse[]
  total: number
  page: number
  page_size: number
}

export const announcementsApi = {
  list: (params?: { type?: string; page?: number; page_size?: number }) => {
    const qs = new URLSearchParams()
    if (params?.type) qs.set('type', params.type)
    if (params?.page) qs.set('page', String(params.page))
    if (params?.page_size) qs.set('page_size', String(params.page_size))
    const query = qs.toString()
    return request<AnnouncementsListResponse>(
      'GET',
      `/announcements/${query ? `?${query}` : ''}`,
    )
  },

  create: async (data: {
    type: string
    title: string
    content: string
    photos?: File[]
  }) => {
    const form = new FormData()
    form.append('type', data.type)
    form.append('title', data.title)
    form.append('content', data.content)
    if (data.photos) {
      for (const photo of data.photos) {
        form.append('photos', photo)
      }
    }
    return request<AnnouncementResponse>('POST', '/announcements/', form)
  },
}
