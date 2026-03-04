import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAnalysis } from '../hooks/useAnalysis'
import { useAnalysisResults } from '../hooks/useAnalysisResults'
import { useRecords } from '../hooks/useRecords'
import { AnalysisResultCard } from '../components/AnalysisResultCard'
import { ApiError } from '../api/types'

export default function AnalysisPage() {
  const queryClient = useQueryClient()
  const { data: allResults = [], isLoading: isLoadingResults, error: resultsError } = useAnalysisResults()

  const handleSuccess = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ['analysisResults'] })
    void queryClient.invalidateQueries({ queryKey: ['records'] })
  }, [queryClient])

  const { mutate, isPending, isError, error } = useAnalysis(handleSuccess)
  const { data: records } = useRecords(1000)

  // Determine if button should be disabled
  const hasPendingRecords = records?.some((r) => r.analysed === false) ?? false
  const isButtonDisabled = isPending || !hasPendingRecords

  // Determine the 413 error case
  const is413Error = isError && error instanceof ApiError && error.status === 413

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
        <p className="mt-1 text-sm text-gray-500">
          Run anomaly detection on unanalysed operational records.
        </p>
      </div>

      {/* Trigger section */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800">Run Analysis</h2>
            {!hasPendingRecords && !isPending && (
              <p className="mt-1 text-sm text-gray-500">No records pending analysis</p>
            )}
          </div>

          <button
            onClick={() => mutate()}
            disabled={isButtonDisabled}
            className={[
              'inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
              isButtonDisabled
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500',
            ].join(' ')}
          >
            {isPending ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Analysing...
              </>
            ) : (
              'Run Analysis'
            )}
          </button>
        </div>

        {/* Error states */}
        {isError && (
          <div className="mt-4 rounded-md border p-4 bg-red-50 border-red-200">
            {is413Error ? (
              <p className="text-sm font-medium text-red-800">
                Data set is too large to analyse
              </p>
            ) : (
              <div>
                <p className="text-sm font-medium text-red-800">Analysis failed</p>
                <p className="mt-1 text-sm text-red-600">
                  {error instanceof ApiError ? error.detail ?? error.message : error?.message ?? 'An unexpected error occurred'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {isLoadingResults && (
        <p className="text-sm text-gray-500">Loading analysis results...</p>
      )}

      {resultsError && (
        <div className="rounded-md border p-4 bg-red-50 border-red-200">
          <p className="text-sm font-medium text-red-800">Failed to load analysis results</p>
          <p className="mt-1 text-sm text-red-600">{resultsError.message}</p>
        </div>
      )}

      {allResults.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Analysis Results
            <span className="ml-2 text-sm font-normal text-gray-400">
              ({allResults.length} result{allResults.length !== 1 ? 's' : ''})
            </span>
          </h2>

          <div className="space-y-4">
            {allResults.map((result, index) => (
              <AnalysisResultCard key={result.id} result={result} index={index} />
            ))}
          </div>
        </div>
      )}

      {!isLoadingResults && allResults.length === 0 && !isPending && (
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-8 text-center">
          <p className="text-sm text-gray-500">No analysis results yet.</p>
          <p className="mt-1 text-xs text-gray-400">
            Click "Run Analysis" to analyse pending records.
          </p>
        </div>
      )}
    </div>
  )
}
