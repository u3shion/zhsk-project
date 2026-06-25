import { useState, useEffect } from 'react'
import { profileApi } from '../api/profile'
import type { ProfileData } from '../api/profile'
import Toast from '../components/Toast'
import './ProfilePage.css'

type NotificationChannel = 'email' | 'sms' | 'vk'

type ToastState = { message: string; type: 'success' | 'error' } | null

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    apartment: '',
    notificationChannel: 'email' as NotificationChannel,
    email: '',
    vkId: '',
  })
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [toast, setToast] = useState<ToastState>(null)

  const [adminSecret, setAdminSecret] = useState('')
  const [upgrading, setUpgrading] = useState(false)

  useEffect(() => {
    profileApi.getMe()
      .then(user => {
        setProfile(user)
        setAvatarUrl(user.avatar_url || null)
        const parts = (user.full_name || '').split(' ')
        setForm({
          firstName: parts[1] || parts[0] || '',
          lastName: parts[0] || '',
          apartment: user.apartment || '',
          notificationChannel: (user.notification_channel as NotificationChannel) || 'email',
          email: user.email || '',
          vkId: user.vk_id || '',
        })
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Ошибка загрузки'))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarUploading(true)
    try {
      const res = await profileApi.uploadAvatar(file)
      setAvatarUrl(res.avatar_url)
      setToast({ message: 'Аватар обновлён', type: 'success' })
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Ошибка загрузки аватара', type: 'error' })
    } finally {
      setAvatarUploading(false)
    }
  }

  const initials = [
    form.lastName ? form.lastName.trim()[0] : "И",
    form.firstName ? form.firstName.trim()[0] : "И",
  ].map(l => (l || '').toUpperCase()).join('') || null

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const fullName = [form.lastName, form.firstName].filter(Boolean).join(' ')
      await profileApi.updateMe({
        full_name: fullName || undefined,
        apartment: form.apartment || undefined,
        notification_channel: form.notificationChannel,
        vk_id: form.vkId || undefined,
        email: form.email || undefined,
      })
      setToast({ message: 'Изменения сохранены', type: 'success' })
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Ошибка сохранения', type: 'error' })
    } finally {
      setSaving(false)
    }
  }

  async function handleUpgrade(e: React.FormEvent) {
    e.preventDefault()
    if (!adminSecret.trim()) return
    setUpgrading(true)
    try {
      const res = await profileApi.upgradeRole({ admin_secret: adminSecret })
      setToast({ message: res.message, type: 'success' })
      setAdminSecret('')
      if (profile) setProfile({ ...profile, role: 'admin' })
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Ошибка', type: 'error' })
    } finally {
      setUpgrading(false)
    }
  }

  if (loading) return <div className="profile-loading">Загрузка...</div>
  if (error && !profile) return <div className="profile-error">{error}</div>

  return (
    <div className="profile-page">
      <h1 className="profile-title">Профиль</h1>

      {profile?.role === 'admin' && (
        <div className="role-badge">Администратор</div>
      )}

      <div className="profile-card">
        <form onSubmit={handleSave} noValidate>
          <div className="avatar-section">
            <label className="avatar-upload-label">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Аватар" className="avatar-placeholder" />
              ) : (
                <div className="avatar-placeholder">{initials}</div>
              )}
              <input
                type="file"
                accept="image/*"
                className="avatar-upload-input"
                onChange={handleAvatarChange}
                disabled={avatarUploading}
              />
            </label>
            {avatarUploading && <span style={{ fontSize: 13, color: '#666' }}>Загрузка...</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="lastName">Фамилия</label>
              <input
                id="lastName"
                name="lastName"
                type="text"
                placeholder="Иванов"
                value={form.lastName}
                onChange={handleChange}
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label htmlFor="firstName">Имя</label>
              <input
                id="firstName"
                name="firstName"
                type="text"
                placeholder="Иван"
                value={form.firstName}
                onChange={handleChange}
                disabled={saving}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="apartment">Номер квартиры</label>
            <input
              id="apartment"
              name="apartment"
              type="text"
              placeholder="12"
              value={form.apartment}
              onChange={handleChange}
              disabled={saving}
            />
          </div>

          <div className="form-group">
            <label htmlFor="notificationChannel">Канал уведомлений</label>
            <select
              id="notificationChannel"
              name="notificationChannel"
              value={form.notificationChannel}
              onChange={handleChange}
              disabled={saving}
            >
              <option value="email">Почта</option>
              <option value="vk">ВКонтакте</option>
            </select>
          </div>

          {form.notificationChannel === 'email' && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                disabled={saving}
              />
            </div>
          )}

          {form.notificationChannel === 'vk' && (
            <div className="form-group">
              <label htmlFor="vkId">VK ID</label>
              <input
                id="vkId"
                name="vkId"
                type="text"
                placeholder="your_vk_id"
                value={form.vkId}
                onChange={handleChange}
                disabled={saving}
              />
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить изменения'}
          </button>
        </form>
      </div>

      {profile?.role !== 'admin' && (
        <div className="profile-card upgrade-card">
          <h2 className="upgrade-title">Повышение прав доступа</h2>
          <p className="upgrade-desc">Введите секретную фразу, чтобы стать администратором.</p>
          <form onSubmit={handleUpgrade} noValidate>
            <div className="form-group">
              <input
                type="password"
                placeholder="Секретная фраза"
                value={adminSecret}
                onChange={e => setAdminSecret(e.target.value)}
                disabled={upgrading}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={upgrading || !adminSecret.trim()}>
              {upgrading ? 'Проверка...' : 'Стать администратором'}
            </button>
          </form>
        </div>
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  )
}
