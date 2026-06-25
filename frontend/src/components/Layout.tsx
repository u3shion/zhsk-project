import { Link, useLocation } from 'react-router-dom'
import ProfileIcon from '../assets/ProfileIcon'
import NewsIcon from '../assets/NewsIcon'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  function isActive(path: string) {
    return location.pathname === path
  }

  function handleLogout() {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">ЖСК-32</div>
        <nav className="sidebar-nav">
          <Link to="/dashboard" className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
            <NewsIcon className="nav-icon" />
            Главная
          </Link>
          <Link to="/profile" className={`nav-item ${isActive('/profile') ? 'active' : ''}`}>
            <ProfileIcon className="nav-icon" />
            Профиль
          </Link>
        </nav>
        <button className="logout-btn" onClick={handleLogout}>
          Выйти
        </button>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
