import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './RoomPage.css'
import { chatApi, type MessageResponse, type RoomResponse } from '../api/chat'
import { profileApi } from '../api/profile'
import Toast from '../components/Toast'
import AddMembersModal from '../components/AddMembersModal'
import ArrowLeftIcon from '../assets/ArrowLeftIcon'

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
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

interface ResolvedMember {
  user_id: number
  full_name: string | null
  apartment: string | null
}

interface ResolvedMessage extends MessageResponse {
  isMine: boolean
  senderName: string | null
  senderApartment: string | null
}

export default function RoomPage() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const room_id = Number(roomId)

  const [room, setRoom] = useState<RoomResponse | null>(null)
  const [messages, setMessages] = useState<ResolvedMessage[]>([])
  const [members, setMembers] = useState<ResolvedMember[]>([])
  const [myProfile, setMyProfile] = useState<{ full_name: string | null; apartment: string | null } | null>(null)
  const [myRole, setMyRole] = useState('resident')
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [showAddMembers, setShowAddMembers] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const membersMapRef = useRef<Map<number, ResolvedMember>>(new Map())
  const myUserIdRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false
    async function init() {
      const token = localStorage.getItem('token') ?? ''
      try {
        const [roomData, membersData, meData] = await Promise.all([
          chatApi.getRoom(room_id),
          chatApi.getMembers(room_id),
          profileApi.getMe(),
        ])
        if (cancelled) return
        setRoom(roomData)
        myUserIdRef.current = meData.id
        setMyProfile({ full_name: meData.full_name, apartment: meData.apartment })
        setMyRole(meData.role)
        setMembers(membersData)
        membersData.forEach(m => membersMapRef.current.set(m.user_id, m))

        const msgs = await chatApi.getMessages(room_id, undefined, 50)
        if (cancelled) return

        const msgsResolved = msgs.reverse().map((msg): ResolvedMessage => {
          const member = membersMapRef.current.get(msg.user_id)
          return {
            ...msg,
            isMine: msg.user_id === meData.id,
            senderName: member?.full_name ?? null,
            senderApartment: member?.apartment ?? null,
          }
        })
        setMessages(msgsResolved)

        const wsUrl = `ws://localhost:8080/ws/rooms/${room_id}?token=${encodeURIComponent(token)}`
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          if (!cancelled) setConnected(true)
        }

        ws.onmessage = (event) => {
          if (cancelled) return
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'message') {
              const member = membersMapRef.current.get(data.user_id)
              const resolved: ResolvedMessage = {
                id: data.id,
                room_id: data.room_id,
                user_id: data.user_id,
                content: data.content,
                created_at: data.created_at,
                is_deleted: false,
                isMine: data.user_id === myUserIdRef.current,
                senderName: member?.full_name ?? null,
                senderApartment: member?.apartment ?? null,
              }
              setMessages(prev => [...prev, resolved])
            } else if (data.type === 'deleted') {
              setMessages(prev =>
                prev.map(m => m.id === data.message_id ? { ...m, is_deleted: true } : m)
              )
            }
          } catch {
            // ignore parse errors
          }
        }

        ws.onerror = () => {
          if (!cancelled) setConnected(false)
        }

        ws.onclose = () => {
          if (!cancelled) setConnected(false)
        }
      } catch {
        if (!cancelled) showToast('Не удалось загрузить чат', 'error')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    init()
    return () => {
      cancelled = true
      wsRef.current?.close()
    }
  }, [room_id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
  }

  function sendMessage() {
    const content = input.trim()
    if (!content || sending || !wsRef.current) return

    setSending(true)
    wsRef.current.send(JSON.stringify({ type: 'message', content }))
    setInput('')
    setSending(false)
    inputRef.current?.focus()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  function getSenderLabel(member: ResolvedMember | undefined) {
    if (!member) return null
    const parts: string[] = []
    if (member.full_name) parts.push(member.full_name)
    if (member.apartment) parts.push(`кв. ${member.apartment}`)
    return parts.length > 0 ? parts.join(' · ') : null
  }

  if (loading) {
    return (
      <div className="room-page">
        <div className="room-loading">Загрузка…</div>
      </div>
    )
  }

  if (!room) {
    return (
      <div className="room-page">
        <div className="room-loading">Чат не найден</div>
      </div>
    )
  }

  return (
    <div className="room-page">
      {/* Header */}
      <div className="room-header">
        <button className="room-back" onClick={() => navigate('/chat')} title="Назад к чатам">
          <ArrowLeftIcon />
        </button>
        <div className="room-header-info">
          <div className="room-header-avatar" style={{ background: getRoomColor(room.name) }}>
            {getRoomInitials(room.name)}
          </div>
          <div className="room-header-text">
            <h2 className="room-header-name">{room.name}</h2>
            <span className="room-header-meta">
              {members.length} {members.length === 1 ? 'участник' : members.length < 5 ? 'участника' : 'участников'}
              {!connected && <span className="room-offline"> · офлайн</span>}
            </span>
          </div>
        </div>
        {myRole === 'admin' && (
          <button
            className="room-add-members-btn"
            onClick={() => setShowAddMembers(true)}
            title="Добавить участников"
          >
            + Участники
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="room-messages">
        {messages.length === 0 ? (
          <div className="room-messages-empty">Начните общение</div>
        ) : (
          messages.map((msg, i) => {
            const prev = messages[i - 1]
            const showDate = !prev || formatDate(msg.created_at) !== formatDate(prev.created_at)
            const senderLabel = getSenderLabel(membersMapRef.current.get(msg.user_id))

            return (
              <div key={msg.id}>
                {showDate && (
                  <div className="room-date-divider">{formatDate(msg.created_at)}</div>
                )}
                <div className={`room-message ${msg.isMine ? 'mine' : 'theirs'} ${msg.is_deleted ? 'deleted' : ''}`}>
                  {!msg.isMine && senderLabel && (
                    <div className="room-message-sender">
                      <span>{senderLabel}</span>
                    </div>
                  )}
                  <div className="room-message-bubble">
                    {msg.is_deleted ? <em>Сообщение удалено</em> : msg.content}
                  </div>
                  <div className="room-message-time">{formatTime(msg.created_at)}</div>
                </div>
              </div>
            )
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="room-input-area">
        {(myProfile !== null && myProfile.full_name && myProfile.apartment) && (
          <textarea
            ref={inputRef}
            className="room-input"
            placeholder="Написать сообщение…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
        )}
        {(myProfile !== null && (!myProfile.full_name || !myProfile.apartment)) && (
          <div className="room-input room-input-disabled">
            Заполните фамилию, имя и номер квартиры в профиле, чтобы отправлять сообщения.
          </div>
        )}
        {(myProfile !== null && myProfile.full_name && myProfile.apartment) && (
          <button
            className="room-send-btn"
            onClick={sendMessage}
            disabled={
              !input.trim() ||
              !connected
            }
            title="Отправить"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        )}
      </div>

      {toast && (
        <Toast message={toast.message} type={toast.type} onDone={() => setToast(null)} />
      )}

      {showAddMembers && (
        <AddMembersModal
          roomId={room_id}
          onClose={() => setShowAddMembers(false)}
          onSuccess={(addedCount) => {
            if (addedCount > 0) {
              showToast(`Добавлен${addedCount === 1 ? '' : 'о'} ${addedCount} участник${addedCount === 1 ? '' : 'а'}`, 'success')
              chatApi.getMembers(room_id).then(members => {
                setMembers(members)
                members.forEach(m => membersMapRef.current.set(m.user_id, m))
              })
            }
          }}
        />
      )}
    </div>
  )
}
