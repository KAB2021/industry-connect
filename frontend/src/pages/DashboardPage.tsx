import { useRecords } from '../hooks/useRecords'
import { useAnalysisResults } from '../hooks/useAnalysisResults'
import { AnalysisResultCard } from '../components/AnalysisResultCard'

interface StatCardProps {
  label: string
  value: string | number
  description?: string
}

function StatCard({ label, value, description }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      {description && (
        <p className="mt-1 text-sm text-gray-500">{description}</p>
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
        <p className="text-gray-500 text-sm">Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4">
        <p className="text-sm font-medium text-red-800">Failed to load records</p>
        <p className="mt-1 text-sm text-red-600">{error.message}</p>
      </div>
    )
  }

  const totalRecords = data?.length ?? 0
  const pendingCount = data?.filter((r) => r.analysed === false).length ?? 0

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      <p className="mt-1 text-sm text-gray-500">
        Summary of the current session's operational records and analysis activity.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Records Loaded"
          value={totalRecords}
          description="Records in the current page"
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
        <h2 className="text-lg font-semibold text-gray-900">Most Recent Analysis Result</h2>
        {analysisError ? (
          <div className="mt-3 rounded-lg bg-red-50 border border-red-200 p-5">
            <p className="text-sm text-red-600">Failed to load analysis results</p>
          </div>
        ) : latestResult ? (
          <div className="mt-3">
            <AnalysisResultCard result={latestResult} index={0} />
          </div>
        ) : (
          <div className="mt-3 rounded-lg bg-gray-50 border border-gray-200 p-5">
            <p className="text-sm text-gray-500">No analysis run yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}
