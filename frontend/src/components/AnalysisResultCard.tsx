import { useState } from 'react'
import type { AnalysisResult, Anomaly } from '../api/types'

interface AnomalyRowProps {
  anomaly: Anomaly
}

function AnomalyRow({ anomaly }: AnomalyRowProps) {
  return (
    <li className="border border-yellow-200 rounded-md p-3 bg-yellow-50">
      <div className="flex flex-wrap gap-2 items-center mb-1">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          {anomaly.metric_name}
        </span>
        <span className="text-xs text-gray-500">Record: {anomaly.record_id}</span>
        <span className="ml-auto text-sm font-semibold text-yellow-900">
          {anomaly.metric_value}
        </span>
      </div>
      <p className="text-sm text-gray-700">{anomaly.explanation}</p>
    </li>
  )
}

interface RecordIdsListProps {
  recordIds: string[]
}

function RecordIdsList({ recordIds }: RecordIdsListProps) {
  const [expanded, setExpanded] = useState(false)
  const SHOW_LIMIT = 5
  const shouldCollapse = recordIds.length > SHOW_LIMIT
  const visibleIds = expanded ? recordIds : recordIds.slice(0, SHOW_LIMIT)

  return (
    <div>
      <ul className="space-y-1">
        {visibleIds.map((id) => (
          <li key={id} className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-0.5 rounded">
            {id}
          </li>
        ))}
      </ul>
      {shouldCollapse && (
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium focus:outline-none"
        >
          {expanded
            ? 'Show less'
            : `Show ${recordIds.length - SHOW_LIMIT} more`}
        </button>
      )}
    </div>
  )
}

interface AnalysisResultCardProps {
  result: AnalysisResult
  index: number
}

export function AnalysisResultCard({ result, index }: AnalysisResultCardProps) {
  const formattedDate = new Date(result.created_at).toLocaleString()

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-gray-700">
          Analysis #{index + 1}
        </h3>
        <span className="text-xs text-gray-400">{formattedDate}</span>
      </div>

      {/* Summary */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Summary</p>
        <p className="text-sm text-gray-800 leading-relaxed">{result.summary}</p>
      </div>

      {/* Anomalies */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Anomalies</p>
        {result.anomalies.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No anomalies detected</p>
        ) : (
          <ul className="space-y-2">
            {result.anomalies.map((anomaly, i) => (
              <AnomalyRow key={`${anomaly.record_id}-${anomaly.metric_name}-${i}`} anomaly={anomaly} />
            ))}
          </ul>
        )}
      </div>

      {/* Token Usage */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Token Usage</p>
        <div className="flex gap-3 flex-wrap">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
            Prompt: {result.prompt_tokens !== null ? result.prompt_tokens.toLocaleString() : 'N/A'}
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
            Completion: {result.completion_tokens !== null ? result.completion_tokens.toLocaleString() : 'N/A'}
          </span>
        </div>
      </div>

      {/* Record IDs */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Records ({result.record_ids.length})
        </p>
        <RecordIdsList recordIds={result.record_ids} />
      </div>
    </div>
  )
}
