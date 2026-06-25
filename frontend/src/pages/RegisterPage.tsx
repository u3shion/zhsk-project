import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../api/auth'
import './auth.css'

export default function RegisterPage() {
  const navigate = useNavigate()

  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    adminSecret: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!form.email || !form.password || !form.confirmPassword) {
      setError('Заполните все обязательные поля')
      return
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setError('Введите корректный email')
      return
    }

    if (form.password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов')
      return
    }

    if (form.password !== form.confirmPassword) {
      setError('Пароли не совпадают')
      return
    }

    setLoading(true)

    try {
      await api.register({
        email: form.email,
        password: form.password,
        admin_secret: form.adminSecret || undefined,
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при регистрации')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="auth-card">
        <div className="success-icon">✓</div>
        <h2>Регистрация прошла успешно!</h2>
        <p>Сейчас вы будете перенаправлены на страницу входа...</p>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <span>ЖСК-32</span>
        </div>
        <h1>Регистрация</h1>

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Почта</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              placeholder="Минимум 6 символов"
              value={form.password}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Подтверждение пароля</label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              placeholder="Повторите пароль"
              value={form.confirmPassword}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="adminSecret">
              Секрет председателя{' '}
              <span className="optional">(только для администраторов)</span>
            </label>
            <input
              id="adminSecret"
              name="adminSecret"
              type="password"
              placeholder="Оставьте пустым, если вы жилец"
              value={form.adminSecret}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="auth-footer">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  )
}
