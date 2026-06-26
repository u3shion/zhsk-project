import { useEffect, useState } from 'react'
import { notificationsApi, type ResidentResponse } from '../api/notifications'

interface NotifyModalProps {
  onClose: () => void
}

type TargetMode = 'all' | 'selected'

const CHANNEL_LABELS: Record<string, string> = {
  email: 'Email',
  sms: 'SMS',
  vk: 'VK',
}

export default function NotifyModal({ onClose }: NotifyModalProps) {
  const [residents, setResidents] = useState<ResidentResponse[]>([])
  const [loadingResidents, setLoadingResidents] = useState(true)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [targetMode, setTargetMode] = useState<TargetMode>('all')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [resultMsg, setResultMsg] = useState('')

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

  async function handleSend() {
    setError('')
    if (!subject.trim()) { setError('Введите заголовок'); return }
    if (!message.trim()) { setError('Введите текст оповещения'); return }

    setSending(true)
    try {
      if (targetMode === 'all') {
        const res = await notificationsApi.broadcast(subject.trim(), message.trim())
        setResultMsg(`Отправлено: ${res.sent}, не доставлено: ${res.failed}`)
      } else {
        if (selected.size === 0) { setError('Выберите хотя бы одного жильца'); setSending(false); return }
        let sent = 0, failed = 0
        for (const id of selected) {
          try {
            await notificationsApi.send(id, subject.trim(), message.trim())
            sent++
          } catch {
            failed++
          }
        }
        setResultMsg(`Отправлено: ${sent}, не доставлено: ${failed}`)
      }
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при отправке')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal modal--notify">
        <div className="modal-header">
          <h2>Отправить оповещение</h2>
          <button className="modal-close" onClick={onClose} aria-label="Закрыть">×</button>
        </div>

        {done ? (
          <div className="notify-done">
            <p className="notify-done-msg">{resultMsg}</p>
            <button className="btn-submit" onClick={onClose}>Закрыть</button>
          </div>
        ) : (
          <div className="modal-form">
            <div className="form-group">
              <label className="form-label">Получатели</label>
              <div className="notify-target-row">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="targetMode"
                    value="all"
                    checked={targetMode === 'all'}
                    onChange={() => setTargetMode('all')}
                  />
                  <span>Все жильцы ({residents.length})</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="targetMode"
                    value="selected"
                    checked={targetMode === 'selected'}
                    onChange={() => setTargetMode('selected')}
                  />
                  <span>Выбрать</span>
                </label>
              </div>

              {targetMode === 'selected' && (
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
                              {r.notification_channel && (
                                <span className="resident-channel">
                                  {CHANNEL_LABELS[r.notification_channel] ?? r.notification_channel}
                                </span>
                              )}
                              <input className="checkbox"
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
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Заголовок</label>
              <input
                type="text"
                className="form-input"
                placeholder="Тема оповещения"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                maxLength={200}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Текст оповещения</label>
              <textarea
                className="form-textarea"
                placeholder="Текст сообщения"
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={4}
              />
            </div>

            {error && <p className="form-error">{error}</p>}

            <div className="modal-footer">
              <button type="button" className="btn-cancel" onClick={onClose}>Отмена</button>
              <button
                type="button"
                className="btn-submit"
                disabled={sending}
                onClick={handleSend}
              >
                {sending ? 'Отправка…' : 'Отправить'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
