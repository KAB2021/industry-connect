import { useQuery } from '@tanstack/react-query'
import { fetchRecords } from '../api/client'
import type { OperationalRecord } from '../api/types'

const POLL_INTERVAL_MS = Number(import.meta.env.VITE_POLL_INTERVAL_MS) || 30000

export function useRecords(limit?: number, offset?: number) {
  const { data, isLoading, error, refetch } = useQuery<OperationalRecord[], Error>({
    queryKey: ['records', limit, offset],
    queryFn: () => fetchRecords(limit, offset),
    refetchInterval: POLL_INTERVAL_MS,
  })

  return { data, isLoading, error, refetch }
}
