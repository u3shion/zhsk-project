const API_BASE = '/api'

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
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

export type MeterType = 'electricity' | 'cold_water' | 'hot_water' | 'heating' | 'gas'

export interface ReadingCreate {
  apartment: string
  period: string
  meter_type: MeterType
  value: number
}

export interface ReadingResponse {
  id: number
  user_id: number
  apartment: string
  period: string
  meter_type: string
  value: number
  submitted_at: string
}

export interface ReadingsListResponse {
  readings: ReadingResponse[]
  total: number
}

export interface ReadingsAllResponse {
  readings: ReadingResponse[]
  total: number
}

export type VerificationMeterType = 'cold_water' | 'hot_water'

export interface VerificationCreate {
  apartment: string
  meter_type: VerificationMeterType
  verification_date: string
}

export interface VerificationResponse {
  id: number
  user_id: number
  apartment: string
  meter_type: string
  verification_date: string
  submitted_at: string
}

export interface VerificationsListResponse {
  verifications: VerificationResponse[]
  total: number
}

export interface VerificationsAllResponse {
  verifications: VerificationResponse[]
  total: number
}

export const metersApi = {
  submit: (data: ReadingCreate) =>
    request<ReadingResponse>('POST', '/readings/', data),

  list: (params?: { period?: string; meter_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.period) qs.set('period', params.period)
    if (params?.meter_type) qs.set('meter_type', params.meter_type)
    const query = qs.toString()
    return request<ReadingsListResponse>(
      'GET',
      `/readings/me${query ? `?${query}` : ''}`,
    )
  },

  listAll: (params?: { period?: string; apartment?: string; meter_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.period) qs.set('period', params.period)
    if (params?.apartment) qs.set('apartment', params.apartment)
    if (params?.meter_type) qs.set('meter_type', params.meter_type)
    const query = qs.toString()
    return request<ReadingsAllResponse>(
      'GET',
      `/readings/all${query ? `?${query}` : ''}`,
    )
  },

  submitVerification: (data: VerificationCreate) =>
    request<VerificationResponse>('POST', '/readings/verifications', data),

  listVerifications: () =>
    request<VerificationsListResponse>('GET', '/readings/verifications/me'),

  listAllVerifications: (params?: { apartment?: string; meter_type?: string }) => {
    const qs = new URLSearchParams()
    if (params?.apartment) qs.set('apartment', params.apartment)
    if (params?.meter_type) qs.set('meter_type', params.meter_type)
    const query = qs.toString()
    return request<VerificationsAllResponse>(
      'GET',
      `/readings/verifications/all${query ? `?${query}` : ''}`,
    )
  },
}

export const METER_TYPE_LABELS: Record<MeterType, string> = {
  electricity: 'Электричество',
  cold_water: 'Холодная вода',
  hot_water: 'Горячая вода',
  heating: 'Отопление',
  gas: 'Газ',
}

export const METER_TYPE_UNITS: Record<MeterType, string> = {
  electricity: 'кВт·ч',
  cold_water: 'м³',
  hot_water: 'м³',
  heating: 'Гкал',
  gas: 'м³',
}

export const METER_TYPE_PLACEHOLDERS: Record<MeterType, string> = {
  electricity: 'например: 12345.67',
  cold_water: 'например: 123.456',
  hot_water: 'например: 98.765',
  heating: 'например: 0.5432',
  gas: 'например: 234.56',
}

export const VERIFICATION_TYPE_LABELS: Record<VerificationMeterType, string> = {
  cold_water: 'Холодная вода',
  hot_water: 'Горячая вода',
}

export type WaterMeterType = 'cold' | 'hot'

export interface WaterMeterCreate {
  apartment: string
  meter_type: WaterMeterType
  serial_number: string
  installed_at: string
  next_verification_at: string
}

export interface WaterMeterUpdate {
  last_verified_at: string
  next_verification_at: string
}

export interface WaterMeterResponse {
  id: number
  user_id: number
  apartment: string
  meter_type: string
  serial_number: string
  installed_at: string
  last_verified_at: string | null
  next_verification_at: string
  is_active: boolean
}

export const WATER_METER_TYPE_LABELS: Record<WaterMeterType, string> = {
  cold: 'Холодная вода',
  hot: 'Горячая вода',
}

export interface WaterMeterVerificationResponse {
  id: number
  apartment: string
  meter_type: string
  serial_number: string
  last_verified_at: string | null
  next_verification_at: string
  is_active: boolean
}

export interface WaterMeterVerificationListResponse {
  verifications: WaterMeterVerificationResponse[]
  total: number
}

export const waterMetersApi = {
  register: (data: WaterMeterCreate) =>
    request<WaterMeterResponse>('POST', '/water-meters/', data),

  list: () =>
    request<WaterMeterResponse[]>('GET', '/water-meters/me'),

  update: (meterId: number, data: WaterMeterUpdate) =>
    request<WaterMeterResponse>('PUT', `/water-meters/${meterId}`, data),

  deactivate: (meterId: number) =>
    request<{ message: string; id: number }>('DELETE', `/water-meters/${meterId}`),

  listAllVerifications: (params?: { apartment?: string; meter_type?: VerificationMeterType }) => {
    const qs = new URLSearchParams()
    if (params?.apartment) qs.set('apartment', params.apartment)
    if (params?.meter_type) {
      qs.set('meter_type', params.meter_type.replace('_water', ''))
    }
    const query = qs.toString()
    return request<WaterMeterVerificationListResponse>(
      'GET',
      `/water-meters/verifications/all${query ? `?${query}` : ''}`,
    )
  },
}
