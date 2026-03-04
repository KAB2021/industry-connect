import { useState, useMemo } from 'react'
import type { OperationalRecord } from '../api/types'

type SortKey = 'timestamp' | 'ingested_at'
type SortDirection = 'asc' | 'desc'
type SourceFilter = 'all' | 'csv' | 'webhook' | 'poll'

function SortIndicator({ col, sortKey, sortDir }: { col: SortKey; sortKey: SortKey; sortDir: SortDirection }) {
  if (sortKey !== col) {
    return <span className="ml-1 text-gray-400">&#8597;</span>
  }
  return (
    <span className="ml-1 text-blue-600">
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
        <span className="text-sm font-medium text-gray-600">Source:</span>
        {sourceOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setSourceFilter(opt.value)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              sourceFilter === opt.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {processed.length === 0 ? (
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-10 text-center">
          <p className="text-gray-500 text-sm">No records found.</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Entity ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Metric Name
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Metric Value
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700"
                  onClick={() => handleSort('timestamp')}
                >
                  Timestamp
                  <SortIndicator col="timestamp" sortKey={sortKey} sortDir={sortDir} />
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Analysed
                </th>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-700"
                  onClick={() => handleSort('ingested_at')}
                >
                  Ingested At
                  <SortIndicator col="ingested_at" sortKey={sortKey} sortDir={sortDir} />
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {processed.map((record, idx) => (
                <tr
                  key={record.id}
                  className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                >
                  <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                    {record.source}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap font-mono">
                    {record.entity_id}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                    {record.metric_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right whitespace-nowrap font-medium">
                    {record.metric_value.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                    {new Date(record.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-center whitespace-nowrap">
                    {record.analysed ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Yes
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
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
