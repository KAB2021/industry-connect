import { useState } from 'react'
import { useRecords } from '../hooks/useRecords'
import RecordsTable from '../components/RecordsTable'

const DEFAULT_LIMIT = 100

export default function RecordsPage() {
  const [limit] = useState(DEFAULT_LIMIT)
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error, refetch } = useRecords(limit, offset)

  const records = data ?? []
  const hasNextPage = records.length >= limit
  const hasPrevPage = offset > 0

  function handlePrev() {
    setOffset((prev) => Math.max(0, prev - limit))
  }

  function handleNext() {
    setOffset((prev) => prev + limit)
  }

  const currentPage = Math.floor(offset / limit) + 1

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-bold text-text-primary tracking-tight">Records</h1>
          <p className="mt-1 text-[13.5px] text-text-muted">
            Operational records ingested from all sources.
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface border border-border text-sm font-medium text-text-secondary hover:bg-surface-hover hover:border-border-hover transition-colors"
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <p className="text-text-muted text-sm">Loading records...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-danger-bg border border-danger-border p-4">
            <p className="text-sm font-medium text-danger">Failed to load records</p>
            <p className="mt-1 text-sm text-danger">{error.message}</p>
          </div>
        ) : (
          <RecordsTable records={records} />
        )}
      </div>

      {/* Pagination controls */}
      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-text-faint">
          Page {currentPage} &mdash; showing records {offset + 1}&ndash;
          {offset + records.length}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            disabled={!hasPrevPage}
            className="px-4 py-2 rounded-lg bg-surface border border-border text-sm font-medium text-text-secondary hover:bg-surface-hover hover:border-border-hover transition-colors disabled:opacity-35 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={handleNext}
            disabled={!hasNextPage}
            className="px-4 py-2 rounded-lg bg-surface border border-border text-sm font-medium text-text-secondary hover:bg-surface-hover hover:border-border-hover transition-colors disabled:opacity-35 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
