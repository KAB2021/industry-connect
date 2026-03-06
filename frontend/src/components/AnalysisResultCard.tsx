import { useState } from 'react'
import type { AnalysisResult, Anomaly } from '../api/types'

interface AnomalyRowProps {
  anomaly: Anomaly
}

function AnomalyRow({ anomaly }: AnomalyRowProps) {
  return (
    <li className="border border-warning-border rounded-lg p-3.5 bg-warning-bg">
      <div className="flex flex-wrap gap-2 items-center mb-1">
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[rgba(245,158,11,0.2)] text-warning">
          {anomaly.metric_name}
        </span>
        <span className="text-[11px] text-text-faint">Record: {anomaly.record_id}</span>
        <span className="ml-auto text-[13px] font-bold text-warning">
          {anomaly.metric_value}
        </span>
      </div>
      <p className="text-[12.5px] text-text-secondary leading-relaxed">{anomaly.explanation}</p>
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
      <div className="flex flex-wrap gap-1.5">
        {visibleIds.map((id) => (
          <span key={id} className="text-[10px] text-text-faint font-mono bg-surface border border-border px-2 py-0.5 rounded">
            {id}
          </span>
        ))}
      </div>
      {shouldCollapse && (
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-2 text-xs text-primary-light hover:text-primary font-medium focus:outline-none"
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
    <div className="bg-surface rounded-xl border border-border backdrop-blur-md transition-colors hover:border-border-hover overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2 px-6 py-4 border-b border-border-light">
        <h3 className="text-sm font-semibold text-text-primary">
          Analysis #{index + 1}
        </h3>
        <span className="text-[11px] text-text-faint">{formattedDate}</span>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Summary */}
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Summary</p>
          <p className="text-[13.5px] text-text-secondary leading-relaxed">{result.summary}</p>
        </div>

        {/* Anomalies */}
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Anomalies</p>
          {result.anomalies.length === 0 ? (
            <p className="text-[13px] text-text-faint italic">No anomalies detected</p>
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
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">Token Usage</p>
          <div className="flex gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-primary-glow text-primary-light border border-border-accent">
              Prompt: {result.prompt_tokens !== null ? result.prompt_tokens.toLocaleString() : 'N/A'}
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-surface text-text-muted border border-border">
              Completion: {result.completion_tokens !== null ? result.completion_tokens.toLocaleString() : 'N/A'}
            </span>
          </div>
        </div>

        {/* Record IDs */}
        <div>
          <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">
            Records ({result.record_ids.length})
          </p>
          <RecordIdsList recordIds={result.record_ids} />
        </div>
      </div>
    </div>
  )
}
