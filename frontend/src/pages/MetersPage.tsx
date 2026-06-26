import { useEffect, useState } from 'react'
import './MetersPage.css'
import {
  metersApi,
  type MeterType,
  METER_TYPE_LABELS,
  METER_TYPE_UNITS,
  METER_TYPE_PLACEHOLDERS,
} from '../api/meters'
import { profileApi } from '../api/profile'
import Toast from '../components/Toast'

const METER_TYPES: MeterType[] = ['electricity', 'cold_water', 'hot_water', 'heating', 'gas']

function formatPeriod(period: string) {
  const [year, month] = period.split('-')
  const date = new Date(Number(year), Number(month) - 1)
  return date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
}

function currentPeriod() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

export default function MetersPage() {
  const [apartment, setApartment] = useState('')
  const [period, setPeriod] = useState(currentPeriod())
  const [meterType, setMeterType] = useState<MeterType>('cold_water')
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [submittedReadings, setSubmittedReadings] = useState<{ meter_type: string; value: number }[]>([])

  useEffect(() => {
    profileApi.getMe().then(u => {
      if (u.apartment) setApartment(u.apartment)
    }).catch(() => {})
    loadReadings()
  }, [])

  async function loadReadings() {
    try {
      const res = await metersApi.list({ period: currentPeriod() })
      setSubmittedReadings(res.readings.map(r => ({ meter_type: r.meter_type, value: r.value })))
    } catch {}
  }

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitError('')

    if (!apartment.trim()) { setSubmitError('Укажите номер квартиры'); return }
    if (!period.match(/^\d{4}-(0[1-9]|1[0-2])$/)) { setSubmitError('Период должен быть в формате ГГГГ-ММ'); return }

    const numValue = parseFloat(value.replace(',', '.'))
    if (isNaN(numValue) || numValue < 0) { setSubmitError('Введите корректное показание (число ≥ 0)'); return }

    setLoading(true)
    try {
      await metersApi.submit({
        apartment: apartment.trim(),
        period,
        meter_type: meterType,
        value: numValue,
      })
      setValue('')
      await loadReadings()
      showToast(`Показание (${METER_TYPE_LABELS[meterType]}) отправлено`, 'success')
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Ошибка при отправке')
    } finally {
      setLoading(false)
    }
  }

  const submittedTypes = new Set(submittedReadings.map(r => r.meter_type))
  const submittedCount = submittedReadings.length

  return (
    <div className="meters-page">
      <div className="meters-header">
        <h1 className="meters-title">Сдача показаний</h1>
        {submittedCount > 0 && (
          <span className="meters-progress">
            {submittedCount} из {METER_TYPES.length} подано за {formatPeriod(currentPeriod())}
          </span>
        )}
      </div>

      <div className="meters-layout">
        <form className="meters-form" onSubmit={handleSubmit} noValidate>
          <div className="form-card">
            <h2 className="form-card-title">Новое показание</h2>

            <div className="form-group">
              <label className="form-label">Период</label>
              <input
                type="month"
                className="form-input period-input"
                value={period}
                max={currentPeriod()}
                onChange={e => setPeriod(e.target.value)}
              />
              <span className="field-hint">Формат: ГГГГ-ММ</span>
            </div>

            <div className="form-group">
              <label className="form-label">Тип счётчика</label>
              <div className="meter-type-grid">
                {METER_TYPES.map(type => (
                  <button
                    key={type}
                    type="button"
                    className={`meter-type-btn ${meterType === type ? 'active' : ''} ${submittedTypes.has(type) ? 'submitted' : ''}`}
                    onClick={() => setMeterType(type)}
                  >
                    {METER_TYPE_LABELS[type]}
                    {submittedTypes.has(type) && <span className="meter-type-check">✓</span>}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                Показания — {METER_TYPE_LABELS[meterType]}
                <span className="field-unit"> ({METER_TYPE_UNITS[meterType]})</span>
              </label>
              <input
                type="text"
                inputMode="decimal"
                className="form-input value-input"
                placeholder={METER_TYPE_PLACEHOLDERS[meterType]}
                value={value}
                onChange={e => setValue(e.target.value)}
              />
              <span className="field-hint">Введите текущее показание счётчика</span>
            </div>

            {submitError && <p className="form-error">{submitError}</p>}

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Отправка…' : 'Отправить показания'}
            </button>
          </div>
        </form>

        <div className="form-card submitted-card">
          <h2 className="form-card-title">Подано за {formatPeriod(currentPeriod())}</h2>
          {submittedReadings.length === 0 ? (
            <p className="no-readings">Пока ничего не подано</p>
          ) : (
            <ul className="readings-list">
              {METER_TYPES.map(type => {
                const reading = submittedReadings.find(r => r.meter_type === type)
                return (
                  <li key={type} className={`reading-item ${reading ? 'has-reading' : 'missing'}`}>
                    <span className="reading-type">{METER_TYPE_LABELS[type as MeterType]}</span>
                    <span className="reading-value">
                      {reading ? `${reading.value.toFixed(2)} ${METER_TYPE_UNITS[type as MeterType]}` : '—'}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>

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
