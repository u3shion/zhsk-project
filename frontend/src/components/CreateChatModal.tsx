import { useEffect, useState } from 'react'
import { notificationsApi, type ResidentResponse } from '../api/notifications'
import { chatApi } from '../api/chat'

interface CreateChatModalProps {
  onClose: () => void
  onSuccess: (roomId: number) => void
}

const AVATAR_COLORS = [
  '#1a3a5c', '#2c5282', '#2b6cb0',
  '#c53030', '#c05621', '#b7791f',
  '#276749', '#2f855a', '#2b6cb0',
  '#6b46c1', '#805ad5', '#9f7aea',
]

export default function CreateChatModal({ onClose, onSuccess }: CreateChatModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [residents, setResidents] = useState<ResidentResponse[]>([])
  const [loadingResidents, setLoadingResidents] = useState(true)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [selectedColor, setSelectedColor] = useState(AVATAR_COLORS[0])
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    notificationsApi.getResidents()
      .then(res => setResidents(res.residents))
      .catch(() => setError('Не удалось загрузить список жильцов'))
      .finally(() => setLoadingResidents(false))
  }, [])

  function toggle(id: number) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function selectAll() {
    setSelected(new Set(residents.map(r => r.id)))
  }

  function selectNone() {
    setSelected(new Set())
  }

  async function handleCreate() {
    setError('')
    if (!name.trim()) { setError('Введите название чата'); return }

    setCreating(true)
    try {
      const room = await chatApi.createRoom({
        name: name.trim(),
        description: description.trim() || undefined,
      })

      for (const userId of selected) {
        try {
          await chatApi.inviteToRoom(room.id, userId)
        } catch {}
      }

      onSuccess(room.id)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при создании чата')
      setCreating(false)
    }
  }

  const initials = name.trim().slice(0, 2).toUpperCase() || '?'

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <h2>Создать чат</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">×</button>
        </div>

        <div className="modal-form">
          {/* Avatar + Name */}
          <div className="form-group">
            <label className="form-label">Название чата</label>
            <div className="chat-modal-name-row">
              <div
                className="chat-avatar-preview"
                style={{ background: selectedColor }}
                title="Цвет аватарки"
              >
                {initials}
              </div>
              <input
                type="text"
                className="form-input"
                placeholder="Например: Общий чат дома"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={100}
                autoFocus
              />
            </div>
          </div>

          {/* Color picker */}
          <div className="form-group">
            <label className="form-label">Цвет аватарки</label>
            <div className="avatar-color-picker">
              {AVATAR_COLORS.map(color => (
                <button
                  key={color}
                  type="button"
                  className={`avatar-color-btn ${selectedColor === color ? 'selected' : ''}`}
                  style={{ background: color }}
                  onClick={() => setSelectedColor(color)}
                  aria-label={`Цвет ${color}`}
                />
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label">Описание <span className="field-hint">(необязательно)</span></label>
            <textarea
              className="form-textarea"
              placeholder="Краткое описание чата"
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              maxLength={300}
            />
          </div>

          {/* Resident selection */}
          <div className="form-group">
            <label className="form-label">Добавить участников</label>
            <div className="notify-residents-box">
              <div className="notify-residents-actions">
                <button type="button" className="link-btn" onClick={selectAll}>Все</button>
                <span className="link-sep">·</span>
                <button type="button" className="link-btn" onClick={selectNone}>Снять</button>
                <span className="link-sep">·</span>
                <span className="notify-selected-count">{selected.size} выбрано</span>
              </div>
              {loadingResidents ? (
                <p className="notify-loading">Загрузка…</p>
              ) : (
                <ul className="notify-residents-list">
                  {residents.map(r => (
                    <li key={r.id}>
                      <label className="resident-label">
                        <div className="resident-info">
                          <span className="resident-name">
                            {r.full_name || `Жилец #${r.id}`}
                          </span>
                          {r.apartment && (
                            <span className="resident-apt">кв. {r.apartment}</span>
                          )}
                          <input
                            className="checkbox"
                            type="checkbox"
                            checked={selected.has(r.id)}
                            onChange={() => toggle(r.id)}
                          />
                        </div>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {error && <p className="form-error">{error}</p>}

          <div className="modal-footer">
            <button type="button" className="btn-cancel" onClick={onClose}>Отмена</button>
            <button
              type="button"
              className="btn-submit"
              disabled={creating || !name.trim()}
              onClick={handleCreate}
            >
              {creating ? 'Создание…' : 'Создать чат'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
