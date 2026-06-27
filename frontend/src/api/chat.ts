const API_BASE = '/api'

function buildHeaders() {
  const headers: Record<string, string> = {}
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

function buildTokenParam(path: string) {
  const sep = path.includes('?') ? '&' : '?'
  return `${sep}token=${localStorage.getItem('token') ?? ''}`
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = { ...buildHeaders() }
  const isFormData = body instanceof FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_BASE}${path}${buildTokenParam(path)}`, {
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

export interface RoomResponse {
  id: number
  name: string
  description: string | null
  created_by: number
  is_active: boolean
  created_at: string
}

export interface CreateRoomData {
  name: string
  description?: string
  member_ids?: number[]
}

export interface MemberResponse {
  user_id: number
  full_name: string | null
  apartment: string | null
  joined_at: string
}

export interface MessageResponse {
  id: number
  room_id: number
  user_id: number
  content: string
  created_at: string
  is_deleted: boolean
}

export const chatApi = {
  getRooms: () => request<RoomResponse[]>('GET', '/rooms/'),

  createRoom: (data: CreateRoomData) =>
    request<RoomResponse>('POST', '/rooms/', data),

  getRoom: (roomId: number) =>
    request<RoomResponse>('GET', `/rooms/${roomId}`),

  inviteToRoom: (roomId: number, userId: number) =>
    request<{ message: string }>('POST', `/rooms/${roomId}/invite`, { user_id: userId }),

  getMembers: (roomId: number) =>
    request<MemberResponse[]>('GET', `/rooms/${roomId}/members`),

  getMessages: (roomId: number, beforeId?: number, limit = 50) => {
    const params = new URLSearchParams({ limit: String(limit) })
    if (beforeId) params.set('before_id', String(beforeId))
    return request<MessageResponse[]>(`GET`, `/rooms/${roomId}/messages?${params}`)
  },

  leaveRoom: (roomId: number) =>
    request<{ message: string }>('DELETE', `/rooms/${roomId}/leave`),
}
