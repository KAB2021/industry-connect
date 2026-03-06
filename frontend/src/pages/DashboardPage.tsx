import { useRecords } from '../hooks/useRecords'
import { useAnalysisResults } from '../hooks/useAnalysisResults'
import { AnalysisResultCard } from '../components/AnalysisResultCard'

interface StatCardProps {
  label: string
  value: string | number
  description?: string
  accent?: boolean
}

function StatCard({ label, value, description, accent }: StatCardProps) {
  return (
    <div
      className={[
        'rounded-xl border backdrop-blur-md p-6 transition-colors',
        accent
          ? 'bg-linear-135/srgb from-primary-glow to-[rgba(16,185,129,0.08)] border-border-accent'
          : 'bg-surface border-border hover:border-border-hover',
      ].join(' ')}
    >
      <p className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">{label}</p>
      <p className={`mt-2 text-3xl font-extrabold tracking-tight ${accent ? 'text-primary-light' : 'text-text-primary'}`}>
        {value}
      </p>
      {description && (
        <p className="mt-1 text-xs text-text-faint">{description}</p>
      )}
    </div>
  )
}

export default function DashboardPage() {
  const { data, isLoading, error } = useRecords(100)
  const { data: analysisResults, error: analysisError } = useAnalysisResults()
  const latestResult = analysisResults?.[0]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className="text-text-muted text-sm">Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-danger-bg border border-danger-border p-4">
        <p className="text-sm font-medium text-danger">Failed to load records</p>
        <p className="mt-1 text-sm text-danger">{error.message}</p>
      </div>
    )
  }

  const totalRecords = data?.length ?? 0
  const pendingCount = data?.filter((r) => r.analysed === false).length ?? 0

  return (
    <div>
      <h1 className="text-[22px] font-bold text-text-primary tracking-tight">Dashboard</h1>
      <p className="mt-1 text-[13.5px] text-text-muted">
        Summary of the current session's operational records and analysis activity.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Records Loaded"
          value={totalRecords}
          description="Records in the current page"
          accent
        />
        <StatCard
          label="Pending Analysis"
          value={pendingCount}
          description="Records not yet analysed"
        />
        <StatCard
          label="Analysed"
          value={totalRecords - pendingCount}
          description="Records that have been analysed"
        />
      </div>

      <div className="mt-8">
        <h2 className="text-[15px] font-semibold text-text-primary mb-3.5">Most Recent Analysis Result</h2>
        {analysisError ? (
          <div className="rounded-lg bg-danger-bg border border-danger-border p-5">
            <p className="text-sm text-danger">Failed to load analysis results</p>
          </div>
        ) : latestResult ? (
          <div>
            <AnalysisResultCard result={latestResult} index={0} />
          </div>
        ) : (
          <div className="rounded-xl bg-surface border border-border p-5">
            <p className="text-sm text-text-muted">No analysis run yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}
