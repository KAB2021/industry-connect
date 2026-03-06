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

  const hasPendingRecords = records?.some((r) => r.analysed === false) ?? false
  const isButtonDisabled = isPending || !hasPendingRecords

  const is413Error = isError && error instanceof ApiError && error.status === 413

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-[22px] font-bold text-text-primary tracking-tight">Analysis</h1>
        <p className="mt-1 text-[13.5px] text-text-muted">
          Run anomaly detection on unanalysed operational records.
        </p>
      </div>

      {/* Trigger section */}
      <div className="bg-surface rounded-xl border border-border backdrop-blur-md p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-[15px] font-semibold text-text-primary">Run Analysis</h2>
            {!hasPendingRecords && !isPending && (
              <p className="mt-1 text-[13px] text-text-muted">No records pending analysis</p>
            )}
          </div>

          <button
            onClick={() => mutate()}
            disabled={isButtonDisabled}
            className={[
              'inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all focus:outline-none',
              isButtonDisabled
                ? 'bg-surface text-text-faint cursor-not-allowed'
                : 'bg-linear-135/srgb from-primary to-secondary text-white shadow-glow hover:shadow-glow-hover',
            ].join(' ')}
          >
            {isPending ? (
              <>
                <svg
                  className="animate-spin h-4 w-4 text-text-faint"
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
          <div className="mt-4 rounded-lg border p-4 bg-danger-bg border-danger-border">
            {is413Error ? (
              <p className="text-sm font-medium text-danger">
                Data set is too large to analyse
              </p>
            ) : (
              <div>
                <p className="text-sm font-medium text-danger">Analysis failed</p>
                <p className="mt-1 text-sm text-danger">
                  {error instanceof ApiError ? error.detail ?? error.message : error?.message ?? 'An unexpected error occurred'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {isLoadingResults && (
        <p className="text-sm text-text-muted">Loading analysis results...</p>
      )}

      {resultsError && (
        <div className="rounded-lg border p-4 bg-danger-bg border-danger-border">
          <p className="text-sm font-medium text-danger">Failed to load analysis results</p>
          <p className="mt-1 text-sm text-danger">{resultsError.message}</p>
        </div>
      )}

      {allResults.length > 0 && (
        <div>
          <h2 className="text-[15px] font-semibold text-text-primary mb-4">
            Analysis Results
            <span className="ml-2 text-xs font-normal text-text-faint">
              ({allResults.length} result{allResults.length !== 1 ? 's' : ''})
            </span>
          </h2>

          <div className="space-y-3.5">
            {allResults.map((result, index) => (
              <AnalysisResultCard key={result.id} result={result} index={index} />
            ))}
          </div>
        </div>
      )}

      {!isLoadingResults && allResults.length === 0 && !isPending && (
        <div className="rounded-xl bg-surface border border-border p-8 text-center">
          <p className="text-sm text-text-muted">No analysis results yet.</p>
          <p className="mt-1 text-xs text-text-faint">
            Click "Run Analysis" to analyse pending records.
          </p>
        </div>
      )}
    </div>
  )
}
