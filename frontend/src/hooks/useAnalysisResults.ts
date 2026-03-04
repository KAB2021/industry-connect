import { useQuery } from '@tanstack/react-query'
import { fetchAnalysisResults } from '../api/client'

export function useAnalysisResults() {
  return useQuery({
    queryKey: ['analysisResults'],
    queryFn: fetchAnalysisResults,
  })
}
