import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './ChatPage.css'
import { chatApi, type RoomResponse } from '../api/chat'
import { profileApi } from '../api/profile'
import CreateChatModal from '../components/CreateChatModal'
import Toast from '../components/Toast'

const AVATAR_COLORS = [
  '#1a3a5c', '#2c5282', '#2b6cb0',
  '#c53030', '#c05621', '#b7791f',
  '#276749', '#2f855a',
  '#6b46c1', '#805ad5', '#9f7aea',
]

function getRoomColor(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

function getRoomInitials(name: string) {
  const words = name.trim().split(/\s+/)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return name.slice(0, 2).toUpperCase()
}

interface RoomWithMembers extends RoomResponse {
  memberCount?: number
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [rooms, setRooms] = useState<RoomWithMembers[]>([])
  const [loading, setLoading] = useState(true)
  const [userRole, setUserRole] = useState('resident')
  const [showModal, setShowModal] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  useEffect(() => {
    profileApi.getMe()
      .then(u => setUserRole(u.role))
      .catch(() => {})
    loadRooms()
  }, [])

  async function loadRooms() {
    setLoading(true)
    try {
      const data = await chatApi.getRooms()
      const withMembers = await Promise.all(
        data.map(async room => {
          try {
            const members = await chatApi.getMembers(room.id)
            return { ...room, memberCount: members.length }
          } catch {
            return { ...room }
          }
        })
      )
      setRooms(withMembers)
    } catch {
      showToast('Не удалось загрузить чаты', 'error')
    } finally {
      setLoading(false)
    }
  }

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
  }

  function handleSuccess() {
    loadRooms()
    showToast('Чат создан', 'success')
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h1 className="chat-title">Чаты</h1>
        {userRole === 'admin' && (
          <button className="publish-btn" onClick={() => setShowModal(true)}>
            + Создать чат
          </button>
        )}
      </div>

      {loading ? (
        <div className="chat-loading">Загрузка…</div>
      ) : rooms.length === 0 ? (
        <div className="chat-empty">
          <p>Пока нет чатов.</p>
          {userRole === 'admin' && <p>Нажмите «Создать чат», чтобы начать.</p>}
        </div>
      ) : (
        <div className="chat-list">
          {rooms.map(room => (
            <div
              key={room.id}
              className="chat-room-card"
              onClick={() => navigate(`/chat/${room.id}`)}
            >
              <div
                className="chat-room-avatar"
                style={{ background: getRoomColor(room.name) }}
              >
                {getRoomInitials(room.name)}
              </div>
              <div className="chat-room-info">
                <p className="chat-room-name">{room.name}</p>
                <div className="chat-room-meta">
                  {room.memberCount !== undefined && (
                    <span className="chat-room-members">
                      {room.memberCount} {room.memberCount === 1 ? 'участник' : room.memberCount < 5 ? 'участника' : 'участников'}
                    </span>
                  )}
                  {room.description && (
                    <span className="chat-room-desc">{room.description}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <CreateChatModal
          onClose={() => setShowModal(false)}
          onSuccess={handleSuccess}
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
