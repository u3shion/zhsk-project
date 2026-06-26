import { Link, useLocation } from 'react-router-dom'
import ProfileIcon from '../assets/ProfileIcon'
import HomeIcon from '../assets/HomeIcon'
import NewsIcon from '../assets/NewsIcon'
import MetersIcon from '../assets/MetersIcon'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  function isActive(path: string) {
    return location.pathname === path
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">ЖСК-32</div>
        <nav className="sidebar-nav">
          <Link to="/dashboard" className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}>
            <HomeIcon className="nav-icon" />
            Главная
          </Link>
          <Link to="/news" className={`nav-item ${isActive('/news') ? 'active' : ''}`}>
            <NewsIcon className="nav-icon" />
            Новости
          </Link>
          <Link to="/meters" className={`nav-item ${isActive('/meters') ? 'active' : ''}`}>
            <MetersIcon className="nav-icon" />
            Показания
          </Link>
          <Link to="/profile" className={`nav-item ${isActive('/profile') ? 'active' : ''}`}>
            <ProfileIcon className="nav-icon" />
            Профиль
          </Link>
        </nav>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
