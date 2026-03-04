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
          <h1 className="text-2xl font-bold text-gray-900">Records</h1>
          <p className="mt-1 text-sm text-gray-500">
            Operational records ingested from all sources.
          </p>
        </div>
        <button
          onClick={() => void refetch()}
          className="inline-flex items-center px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <p className="text-gray-500 text-sm">Loading records...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4">
            <p className="text-sm font-medium text-red-800">Failed to load records</p>
            <p className="mt-1 text-sm text-red-600">{error.message}</p>
          </div>
        ) : (
          <RecordsTable records={records} />
        )}
      </div>

      {/* Pagination controls */}
      <div className="mt-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Page {currentPage} &mdash; showing records {offset + 1}&ndash;
          {offset + records.length}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            disabled={!hasPrevPage}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={handleNext}
            disabled={!hasNextPage}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
