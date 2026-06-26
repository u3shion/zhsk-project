import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  metersApi,
  type MeterType,
  type ReadingResponse,
  METER_TYPE_LABELS,
  METER_TYPE_UNITS,
} from '../api/meters'
import Toast from '../components/Toast'
import './MetersAdminPage.css'

type SortKey = 'apartment' | 'period' | 'meter_type' | 'value' | 'submitted_at'
type SortDir = 'asc' | 'desc'

function currentPeriod() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function downloadCSV(readings: ReadingResponse[], period: string) {
  const headers = ['Квартира', 'Период', 'Тип счётчика', 'Показание', 'Единица', 'Время подачи']
  const rows = readings.map(r => [
    r.apartment,
    r.period,
    METER_TYPE_LABELS[r.meter_type as MeterType] ?? r.meter_type,
    r.value,
    METER_TYPE_UNITS[r.meter_type as MeterType] ?? '',
    formatDate(r.submitted_at),
  ])
  const csv = [headers, ...rows]
    .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `meters_${period}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function formatPeriodLong(period: string) {
  const [year, month] = period.split('-')
  return new Date(Number(year), Number(month) - 1).toLocaleDateString('ru-RU', {
    month: 'long',
    year: 'numeric',
  })
}

export default function MetersAdminPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialPeriod = searchParams.get('period') ?? currentPeriod()

  const [allReadings, setAllReadings] = useState<ReadingResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Filters (server-side)
  const [period, setPeriod] = useState(initialPeriod)
  const [meterTypeFilter, setMeterTypeFilter] = useState<string>('')

  // Filter (client-side)
  const [apartmentFilter, setApartmentFilter] = useState('')

  // Sort
  const [sortKey, setSortKey] = useState<SortKey>('apartment')
  const [sortDir, setSortDir] = useState<SortDir>('asc')

  async function load() {
    setLoading(true)
    try {
      const params: Parameters<typeof metersApi.listAll>[0] = { period }
      if (meterTypeFilter) params.meter_type = meterTypeFilter
      const res = await metersApi.listAll(params)
      setAllReadings(res.readings)
    } catch (err) {
      setToast({ message: err instanceof Error ? err.message : 'Ошибка загрузки', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, meterTypeFilter])

  function showToast(message: string, type: 'success' | 'error') {
    setToast({ message, type })
  }

  const filtered = useMemo(() => {
    const base = apartmentFilter
      ? allReadings.filter(r =>
          r.apartment.toLowerCase().includes(apartmentFilter.toLowerCase()),
        )
      : allReadings

    return [...base].sort((a, b) => {
      let av: string | number = ''
      let bv: string | number = ''
      switch (sortKey) {
        case 'apartment':
          av = a.apartment; bv = b.apartment; break
        case 'period':
          av = a.period; bv = b.period; break
        case 'meter_type':
          av = a.meter_type; bv = b.meter_type; break
        case 'value':
          av = a.value; bv = b.value; break
        case 'submitted_at':
          av = a.submitted_at; bv = b.submitted_at; break
      }
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [allReadings, apartmentFilter, sortKey, sortDir])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  function SortIcon({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="sort-icon neutral">⇅</span>
    return <span className="sort-icon active">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  // Per-type grouping per apartment+period
  const submittedTypes = useMemo(() => {
    const map: Record<string, Set<string>> = {}
    for (const r of allReadings) {
      const key = `${r.apartment}||${r.period}`
      map[key] ??= new Set()
      map[key].add(r.meter_type)
    }
    return map
  }, [allReadings])

  const METER_TYPES: MeterType[] = ['electricity', 'cold_water', 'hot_water', 'heating', 'gas']

  // Unique apartments with their submission status
  const apartments = useMemo(() => {
    const map: Record<string, { submitted: string[]; missing: string[] }> = {}
    for (const r of allReadings) {
      const key = `${r.apartment}||${r.period}`
      map[r.apartment] ??= { submitted: [], missing: [] }
      map[r.apartment].submitted.push(r.meter_type)
    }
    for (const apt of Object.keys(map)) {
      map[apt].missing = METER_TYPES.filter(
        t => !(map[apt].submitted as string[]).includes(t),
      )
    }
    return map
  }, [allReadings])

  const aptCount = Object.keys(apartments).length
  const completeCount = Object.values(apartments).filter(a => a.missing.length === 0).length

  function handlePeriodChange(p: string) {
    setPeriod(p)
    setSearchParams({ period: p })
  }

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h1 className="admin-title">Сводная таблица показаний</h1>
        <span className="admin-period-badge">
          {formatPeriodLong(period)}
        </span>
      </div>

      {/* Summary strip */}
      <div className="admin-summary">
        <div className="summary-stat">
          <span className="stat-value">{aptCount}</span>
          <span className="stat-label">квартир</span>
        </div>
        <div className="summary-stat complete">
          <span className="stat-value">{completeCount}</span>
          <span className="stat-label">полных</span>
        </div>
        <div className="summary-stat">
          <span className="stat-value">{allReadings.length}</span>
          <span className="stat-label">показаний</span>
        </div>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <div className="filter-group">
          <label className="filter-label">Период</label>
          <input
            type="month"
            className="filter-input"
            value={period}
            max={currentPeriod()}
            onChange={e => handlePeriodChange(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Тип счётчика</label>
          <select
            className="filter-select"
            value={meterTypeFilter}
            onChange={e => setMeterTypeFilter(e.target.value)}
          >
            <option value="">Все</option>
            {METER_TYPES.map(t => (
              <option key={t} value={t}>{METER_TYPE_LABELS[t]}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Квартира</label>
          <input
            type="text"
            className="filter-input"
            placeholder="Поиск…"
            value={apartmentFilter}
            onChange={e => setApartmentFilter(e.target.value)}
          />
        </div>

        <button
          className="btn-export"
          onClick={() => {
            if (filtered.length === 0) {
              showToast('Нет данных для экспорта', 'error')
              return
            }
            downloadCSV(filtered, period)
            showToast(`Скачано ${filtered.length} строк`, 'success')
          }}
        >
          Скачать CSV
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="admin-loading">Загрузка…</div>
      ) : filtered.length === 0 ? (
        <div className="admin-empty">Нет показаний за этот период</div>
      ) : (
        <div className="table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th onClick={() => toggleSort('apartment')}>
                  Квартира <SortIcon col="apartment" />
                </th>
                <th onClick={() => toggleSort('period')}>
                  Период <SortIcon col="period" />
                </th>
                <th onClick={() => toggleSort('meter_type')}>
                  Тип <SortIcon col="meter_type" />
                </th>
                <th onClick={() => toggleSort('value')}>
                  Показание <SortIcon col="value" />
                </th>
                <th onClick={() => toggleSort('submitted_at')}>
                  Время подачи <SortIcon col="submitted_at" />
                </th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(r => {
                const aptKey = `${r.apartment}||${r.period}`
                const aptSubmitted = submittedTypes[aptKey]
                const isComplete = aptSubmitted && aptSubmitted.size === METER_TYPES.length
                return (
                  <tr key={r.id}>
                    <td className="td-apartment">{r.apartment}</td>
                    <td>{formatPeriodLong(r.period)}</td>
                    <td>{METER_TYPE_LABELS[r.meter_type as MeterType] ?? r.meter_type}</td>
                    <td className="td-value">
                      {r.value.toFixed(2)} {METER_TYPE_UNITS[r.meter_type as MeterType]}
                    </td>
                    <td className="td-date">{formatDate(r.submitted_at)}</td>
                    <td>
                      {isComplete ? (
                        <span className="badge complete">✓ Все подано</span>
                      ) : aptSubmitted ? (
                        <span className="badge partial">
                          {aptSubmitted.size}/{METER_TYPES.length}
                        </span>
                      ) : (
                        <span className="badge missing">—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
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
