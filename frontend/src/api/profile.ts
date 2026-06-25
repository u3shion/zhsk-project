export interface ProfileData {
  id: number
  email: string
  role: string
  full_name: string | null
  apartment: string | null
  notification_channel: string
  phone: string | null
  vk_id: string | null
  avatar_url: string | null
}

export interface ProfileUpdateData {
  full_name?: string
  apartment?: string
  notification_channel?: 'email' | 'sms' | 'vk'
  phone?: string
  vk_id?: string
  email?: string
}

export interface RoleUpgradeData {
  admin_secret: string
}

export interface RoleUpgradeResponse {
  message: string
  role: string
}

const API_BASE = '/api'

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json().catch(() => ({ detail: null }))

  if (!res.ok) {
    throw new Error(
      typeof data?.detail === 'string' && data.detail
        ? data.detail
        : `Ошибка ${res.status}`,
    )
  }

  return data as T
}

export const profileApi = {
  getMe: () => request<ProfileData>('GET', '/users/me'),

  updateMe: (data: ProfileUpdateData) =>
    request<{ message: string }>('PUT', '/users/me', data),

  upgradeRole: (data: RoleUpgradeData) =>
    request<RoleUpgradeResponse>('POST', '/users/me/upgrade-role', data),

  uploadAvatar: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('token')
    return fetch(`${API_BASE}/users/me/avatar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }).then(async res => {
      const data = await res.json().catch(() => ({ detail: null }))
      if (!res.ok) {
        throw new Error(
          typeof data?.detail === 'string' && data.detail
            ? data.detail
            : `Ошибка ${res.status}`,
        )
      }
      return data as { avatar_url: string }
    })
  },
}
