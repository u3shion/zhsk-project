const API_BASE = '/api'

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {}
  const isFormData = body instanceof FormData
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }
  const token = localStorage.getItem('token')
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

export interface ResidentResponse {
  id: number
  full_name: string | null
  apartment: string | null
  notification_channel: string | null
  email: string | null
  phone: string | null
  vk_id: string | null
}

export interface ResidentsResponse {
  residents: ResidentResponse[]
}

export interface SendResult {
  status: string
  channel: string
  recipient: string
  error: string | null
}

export interface BroadcastResult {
  sent: number
  failed: number
}

export const notificationsApi = {
  getResidents: () => request<ResidentsResponse>('GET', '/notifications/residents'),

  send: (userId: number, subject: string, message: string) =>
    request<SendResult>('POST', '/notifications/send', { user_id: userId, subject, message }),

  broadcast: (subject: string, message: string) =>
    request<BroadcastResult>('POST', '/notifications/broadcast', { subject, message }),
}
