import { useEffect, useRef, useState } from 'react'

interface ToastProps {
  message: string
  type?: 'success' | 'error'
  onDone: () => void
}

export default function Toast({ message, type = 'success', onDone }: ToastProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout>>(null)
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    timerRef.current = setTimeout(() => setLeaving(true), 2000)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  const handleAnimationEnd = () => {
    if (leaving) onDone()
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 24,
        right: 20,
        background: type === 'error' ? '#c0392b' : '#27ae60',
        color: '#fff',
        padding: '12px 24px',
        borderRadius: '8px',
        fontSize: 15,
        fontWeight: 500,
        boxShadow: '-4px 4px 16px rgba(0,0,0,0.15)',
        zIndex: 9999,
        animation: leaving ? 'toastSlideOut 0.3s ease forwards' : 'toastSlideIn 0.25s ease',
      }}
      onAnimationEnd={handleAnimationEnd}
    >
      {message}
    </div>
  )
}
