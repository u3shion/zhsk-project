const API_BASE = '/api'

export interface RegisterData {
  email: string
  password: string
  admin_secret?: string
}

export interface LoginData {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface RegisterResponse {
  message: string
  role: string
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  auth: boolean = true,
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  if (auth) {
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
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

export const api = {
  register: (data: RegisterData) =>
    request<RegisterResponse>('POST', '/auth/register', data),

  login: (data: LoginData) =>
    request<AuthResponse>('POST', '/auth/login', data),
}

export function isAdmin(): boolean {
  const token = localStorage.getItem('token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role === 'admin'
  } catch {
    return false
  }
}
