import { useEffect, useState } from 'react'
import { notificationsApi, type ResidentResponse } from '../api/notifications'
import { chatApi } from '../api/chat'

interface AddMembersModalProps {
  roomId: number
  onClose: () => void
  onSuccess: (addedCount: number) => void
}

export default function AddMembersModal({ roomId, onClose, onSuccess }: AddMembersModalProps) {
  const [residents, setResidents] = useState<ResidentResponse[]>([])
  const [currentMembers, setCurrentMembers] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      notificationsApi.getResidents(),
      chatApi.getMembers(roomId),
    ])
      .then(([res, members]) => {
        setResidents(res.residents)
        setCurrentMembers(new Set(members.map(m => m.user_id)))
      })
      .catch(() => setError('Не удалось загрузить список жильцов'))
      .finally(() => setLoading(false))
  }, [roomId])

  const available = residents.filter(r => !currentMembers.has(r.id))

  function toggle(id: number) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function selectAll() {
    setSelected(new Set(available.map(r => r.id)))
  }

  function selectNone() {
    setSelected(new Set())
  }

  async function handleAdd() {
    setError('')
    if (selected.size === 0) { setError('Выберите хотя бы одного жильца'); return }

    setSending(true)
    let added = 0
    for (const userId of selected) {
      try {
        await chatApi.inviteToRoom(roomId, userId)
        added++
      } catch {
        // Skip failed invites
      }
    }
    setSending(false)
    onSuccess(added)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <h2>Добавить участников</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">×</button>
        </div>

        <div className="modal-form">
          {loading ? (
            <p className="notify-loading">Загрузка…</p>
          ) : available.length === 0 ? (
            <p className="notify-loading">Все жильцы уже состоят в этом чате.</p>
          ) : (
            <div className="form-group">
              <div className="notify-residents-box">
                <div className="notify-residents-actions">
                  <button type="button" className="link-btn" onClick={selectAll}>Все</button>
                  <span className="link-sep">·</span>
                  <button type="button" className="link-btn" onClick={selectNone}>Снять</button>
                  <span className="link-sep">·</span>
                  <span className="notify-selected-count">{selected.size} выбрано</span>
                </div>
                <ul className="notify-residents-list">
                  {available.map(r => (
                    <li key={r.id}>
                      <label className="resident-label">
                        <div className="resident-info">
                          <span className="resident-name">
                            {r.full_name || `Жилец #${r.id}`}
                          </span>
                          {r.apartment && (
                            <span className="resident-apt">кв. {r.apartment}</span>
                          )}
                          {r.notification_channel && (
                            <span className="resident-channel">
                              {r.notification_channel}
                            </span>
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
              </div>
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <div className="modal-footer">
            <button type="button" className="btn-cancel" onClick={onClose}>Отмена</button>
            <button
              type="button"
              className="btn-submit"
              disabled={sending || available.length === 0 || selected.size === 0}
              onClick={handleAdd}
            >
              {sending ? 'Добавление…' : 'Добавить'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
