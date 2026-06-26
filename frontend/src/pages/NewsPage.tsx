import { useEffect, useRef, useState } from 'react'
import './NewsPage.css'
import { announcementsApi, type AnnouncementResponse } from '../api/announcements'
import { profileApi } from '../api/profile'
import Toast from '../components/Toast'

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

interface ModalProps {
  onClose: () => void
  onSuccess: () => void
  userRole: string
}

function CreateModal({ onClose, onSuccess, userRole }: ModalProps) {
  const isAdmin = userRole === 'admin'
  const [type, setType] = useState<'news' | 'ad'>(isAdmin ? 'news' : 'ad')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [photos, setPhotos] = useState<File[]>([])
  const [photoPreviews, setPhotoPreviews] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    const newFiles = [...photos, ...files]
    setPhotos(newFiles)
    const newPreviews = newFiles.map(f => URL.createObjectURL(f))
    setPhotoPreviews(newPreviews)
    if (fileRef.current) fileRef.current.value = ''
  }

  function removePhoto(index: number) {
    setPhotos(prev => prev.filter((_, i) => i !== index))
    setPhotoPreviews(prev => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!title.trim()) { setError('Введите название'); return }
    if (!content.trim()) { setError('Введите текст объявления'); return }

    setLoading(true)
    try {
      await announcementsApi.create({
        type,
        title: title.trim(),
        content: content.trim(),
        photos,
      })
      onSuccess()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <h2>Новая публикация</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {isAdmin && (
            <div className="form-group">
              <label className="form-label">Тип</label>
              <div className="type-selector">
                <button
                  type="button"
                  className={`type-btn ${type === 'news' ? 'active' : ''}`}
                  onClick={() => setType('news')}
                >
                  Новость
                </button>
                <button
                  type="button"
                  className={`type-btn ${type === 'ad' ? 'active' : ''}`}
                  onClick={() => setType('ad')}
                >
                  Объявление
                </button>
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Название</label>
            <input
              type="text"
              className="form-input"
              placeholder="Заголовок публикации"
              value={title}
              onChange={e => setTitle(e.target.value)}
              maxLength={200}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Текст</label>
            <textarea
              className="form-textarea"
              placeholder="Текст публикации"
              value={content}
              onChange={e => setContent(e.target.value)}
              rows={5}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Фото</label>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              style={{ display: 'none' }}
              onChange={handlePhotoChange}
            />
            <button
              type="button"
              className="photo-btn"
              onClick={() => fileRef.current?.click()}
            >
              {photos.length > 0 ? `Добавить ещё фото (${photos.length})` : 'Прикрепить фото'}
            </button>
            {photoPreviews.length > 0 && (
              <div className="photo-previews-grid">
                {photoPreviews.map((src, i) => (
                  <div key={i} className="photo-preview-wrap">
                    <img src={src} alt={`Фото ${i + 1}`} className="photo-preview" />
                    <button
                      type="button"
                      className="photo-remove"
                      onClick={() => removePhoto(i)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {error && <p className="form-error">{error}</p>}

          <div className="modal-footer">
            <button type="button" className="btn-cancel" onClick={onClose}>Отмена</button>
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Публикация…' : 'Опубликовать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function NewsPage() {
  const [news, setNews] = useState<AnnouncementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [userRole, setUserRole] = useState<string>('resident')

  useEffect(() => {
    profileApi.getMe().then(u => setUserRole(u.role)).catch(() => {})
    loadNews()
  }, [])

  async function loadNews() {
    setLoading(true)
    try {
      const res = await announcementsApi.list({ page_size: 50 })
      setNews(res.items)
    } catch {
      showToast('Не удалось загрузить новости', 'error')
    } finally {
      setLoading(false)
    }
  }

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
  }

  function handleSuccess() {
    loadNews()
    showToast('Публикация создана', 'success')
  }

  return (
    <div className="news-page">
      <div className="news-header">
        <h1 className="news-title">Новости</h1>
        <button className="publish-btn" onClick={() => setShowModal(true)}>
          + Новая публикация
        </button>
      </div>

      {loading ? (
        <div className="news-loading">Загрузка…</div>
      ) : news.length === 0 ? (
        <div className="news-empty">
          <p>Пока нет публикаций.</p>
          <p>Будьте первым — опубликуйте новость!</p>
        </div>
      ) : (
        <div className="news-feed">
          {news.map(item => (
            <article key={item.id} className="news-card">
              {item.photo_urls && item.photo_urls.length > 0 && (
                <div className={`news-card-photos news-card-photos--${item.photo_urls.length}`}>
                  {item.photo_urls.map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      alt={`${item.title} — фото ${i + 1}`}
                      className="news-card-img"
                      onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                    />
                  ))}
                </div>
              )}
              <div className="news-card-body">
                <div className="news-card-meta">
                  <span className={`news-badge news-badge--${item.type}`}>
                    {item.type === 'news' ? 'Новость' : 'Объявление'}
                  </span>
                  <span className="news-date">{formatDate(item.created_at)}</span>
                </div>
                <h2 className="news-card-title">{item.title}</h2>
                <p className="news-card-text">{item.content}</p>
              </div>
            </article>
          ))}
        </div>
      )}

      {showModal && (
        <CreateModal
          onClose={() => setShowModal(false)}
          onSuccess={handleSuccess}
          userRole={userRole}
        />
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
