import { useEffect, useState } from 'react'
import {
  metersApi,
  waterMetersApi,
  type WaterMeterResponse,
  METER_TYPE_LABELS,
  METER_TYPE_UNITS,
  WATER_METER_TYPE_LABELS,
} from '../api/meters'
import { announcementsApi, type AnnouncementResponse } from '../api/announcements'
import './DashboardPage.css'

const METER_TYPES = ['electricity', 'cold_water', 'hot_water', 'heating', 'gas'] as const

function currentPeriod() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatPeriod(period: string) {
  const [year, month] = period.split('-')
  const date = new Date(Number(year), Number(month) - 1)
  return date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export default function DashboardPage() {
  const [news, setNews] = useState<AnnouncementResponse[]>([])
  const [newsLoading, setNewsLoading] = useState(true)
  const [readings, setReadings] = useState<{ meter_type: string; value: number }[]>([])
  const [readingsLoading, setReadingsLoading] = useState(true)
  const [waterMeters, setWaterMeters] = useState<WaterMeterResponse[]>([])
  const [metersLoading, setMetersLoading] = useState(true)

  useEffect(() => {
    loadNews()
    loadReadings()
    loadWaterMeters()
  }, [])

  async function loadNews() {
    try {
      const res = await announcementsApi.list({ type: 'news', page_size: 5 })
      setNews(res.items)
    } catch {
      // silent fail
    } finally {
      setNewsLoading(false)
    }
  }

  async function loadReadings() {
    try {
      const res = await metersApi.list({ period: currentPeriod() })
      setReadings(res.readings.map(r => ({ meter_type: r.meter_type, value: r.value })))
    } catch {
      // silent fail
    } finally {
      setReadingsLoading(false)
    }
  }

  async function loadWaterMeters() {
    try {
      const res = await waterMetersApi.list()
      setWaterMeters(res)
    } catch {
      // silent fail
    } finally {
      setMetersLoading(false)
    }
  }

  const period = formatPeriod(currentPeriod())

  return (
    <div className="dashboard">
      {/* Новости */}
      <section className="dashboard-section">
        <h2 className="section-title">Последние новости</h2>
        {newsLoading ? (
          <div className="card-loading">Загрузка…</div>
        ) : news.length === 0 ? (
          <div className="card-empty">Новостей пока нет</div>
        ) : (
          <div className="news-list">
            {news.map(item => (
              <article key={item.id} className="news-item">
                {item.photo_urls && item.photo_urls.length > 0 && (
                  <img
                    src={item.photo_urls[0]}
                    alt=""
                    className="news-item-img"
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                )}
                <div className="news-item-body">
                  <div className="news-item-date">{formatDate(item.created_at)}</div>
                  <h3 className="news-item-title">{item.title}</h3>
                  <p className="news-item-text">{item.content}</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Показания за этот месяц */}
      <section className="dashboard-section">
        <section className="dashboard-section">
          <h2 className="section-title">Подано за {period}</h2>
          <div className="dashboard-card">
            {readingsLoading ? (
              <div className="card-loading">Загрузка…</div>
            ) : readings.length === 0 ? (
              <p className="no-readings">Пока ничего не подано</p>
            ) : (
              <ul className="readings-list">
                {METER_TYPES.map(type => {
                  const reading = readings.find(r => r.meter_type === type)
                  return (
                    <li key={type} className={`reading-item ${reading ? 'has-reading' : 'missing'}`}>
                      <span className="reading-type">{METER_TYPE_LABELS[type]}</span>
                      <span className="reading-value">
                        {reading
                          ? `${reading.value.toFixed(2)} ${METER_TYPE_UNITS[type]}`
                          : '—'}
                      </span>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </section>

        {/* Счётчики воды */}
        <section className="dashboard-section">
          <h2 className="section-title">Мои счётчики воды</h2>
          <div className="dashboard-card">
            {metersLoading ? (
              <div className="card-loading">Загрузка…</div>
            ) : waterMeters.length === 0 ? (
              <p className="no-readings">Нет зарегистрированных счётчиков воды</p>
            ) : (
              <ul className="readings-list">
                {waterMeters.map(m => {
                  const next = new Date(m.next_verification_at).toLocaleDateString('ru-RU')
                  const daysLeft = Math.ceil(
                    (new Date(m.next_verification_at).getTime() - Date.now()) / 86400000,
                  )
                  const isOverdue = daysLeft < 0
                  return (
                    <li key={m.id} className={`reading-item ${isOverdue ? 'missing' : 'has-reading'}`}>
                      <span className="reading-type">
                        {WATER_METER_TYPE_LABELS[m.meter_type as 'cold' | 'hot'] ?? m.meter_type}
                        <br />
                        <span className="serial-number">{m.serial_number}</span>
                      </span>
                      <span className="reading-value">
                        <span style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                          <span>{next}</span>
                          {isOverdue && (
                            <span className="meter-status overdue">Просрочена</span>
                          )}
                          {!isOverdue && daysLeft <= 60 && (
                            <span className="meter-status warning">{daysLeft} дн.</span>
                          )}
                        </span>
                      </span>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </section>
      </section>

    </div>
  )
}
