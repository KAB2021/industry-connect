import { useState, useMemo } from 'react'
import type { OperationalRecord } from '../api/types'

type SortKey = 'timestamp' | 'ingested_at'
type SortDirection = 'asc' | 'desc'
type SourceFilter = 'all' | 'csv' | 'webhook' | 'poll'

function SortIndicator({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDirection }) {
  if (sortKey !== col) {
    return <span className="ml-1 text-text-faint">&#8597;</span>
  }
  return (
    <span className="ml-1 text-primary-light">
      {sortDir === 'asc' ? '\u2191' : '\u2193'}
    </span>
  )
}

interface RecordsTableProps {
  records: OperationalRecord[]
}

export default function RecordsTable({ records }: RecordsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('timestamp')
  const [sortDir, setSortDir] = useState<SortDirection>('desc')
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const processed = useMemo(() => {
    let result = records

    if (sourceFilter !== 'all') {
      result = result.filter((r) => r.source === sourceFilter)
    }

    result = [...result].sort((a, b) => {
      const aVal = new Date(a[sortKey]).getTime()
      const bVal = new Date(b[sortKey]).getTime()
      return sortDir === 'asc' ? aVal - bVal : bVal - aVal
    })

    return result
  }, [records, sourceFilter, sortKey, sortDir])

  const sourceOptions: { value: SourceFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'csv', label: 'CSV' },
    { value: 'webhook', label: 'Webhook' },
    { value: 'poll', label: 'Poll' },
  ]

  return (
    <div>
      {/* Source filter */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xs font-medium text-text-muted">Source:</span>
        {sourceOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setSourceFilter(opt.value)}
            className={`px-3.5 py-1 rounded-full text-xs font-medium transition-colors border ${
              sourceFilter === opt.value
                ? 'bg-primary-glow text-primary-light border-border-accent'
                : 'bg-transparent text-text-muted border-border hover:bg-surface hover:text-text-secondary'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {processed.length === 0 ? (
        <div className="rounded-xl bg-surface border border-border p-10 text-center">
          <p className="text-text-muted text-sm">No records found.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border bg-surface">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-white/[2%]">
              <tr>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-text-muted uppercase tracking-wide">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-text-muted uppercase tracking-wide">
                  Entity ID
                </th>
                <th className="px-4 py-3 text-left text-[11px] font-semibold text-text-muted uppercase tracking-wide">
                  Metric Name
                </th>
                <th className="px-4 py-3 text-right text-[11px] font-semibold text-text-muted uppercase tracking-wide">
                  Metric Value
                </th>
                <th
                  className="px-4 py-3 text-left text-[11px] font-semibold text-text-muted uppercase tracking-wide cursor-pointer select-none hover:text-text-secondary"
                  onClick={() => handleSort('timestamp')}
                >
                  Timestamp
                  <SortIndicator col="timestamp" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className="px-4 py-3 text-center text-[11px] font-semibold text-text-muted uppercase tracking-wide">
                  Analysed
                </th>
                <th
                  className="px-4 py-3 text-left text-[11px] font-semibold text-text-muted uppercase tracking-wide cursor-pointer select-none hover:text-text-secondary"
                  onClick={() => handleSort('ingested_at')}
                >
                  Ingested At
                  <SortIndicator col="ingested_at" sortKey={sortKey} sortDir={sortDir} />
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light">
              {processed.map((record, idx) => (
                <tr
                  key={record.id}
                  className={`${idx % 2 === 0 ? 'bg-transparent' : 'bg-white/[2%]'} hover:bg-white/[2%]`}
                >
                  <td className="px-4 py-3 text-[13px] text-text-secondary whitespace-nowrap">
                    {record.source}
                  </td>
                  <td className="px-4 py-3 text-xs text-text-muted whitespace-nowrap font-mono">
                    {record.entity_id}
                  </td>
                  <td className="px-4 py-3 text-[13px] text-text-secondary whitespace-nowrap">
                    {record.metric_name}
                  </td>
                  <td className="px-4 py-3 text-[13px] text-text-primary text-right whitespace-nowrap font-semibold">
                    {record.metric_value.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-[13px] text-text-secondary whitespace-nowrap">
                    {new Date(record.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-center whitespace-nowrap">
                    {record.analysed ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-success-bg text-success border border-success-border">
                        Analysed
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-warning-bg text-warning border border-warning-border">
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[13px] text-text-secondary whitespace-nowrap">
                    {new Date(record.ingested_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
