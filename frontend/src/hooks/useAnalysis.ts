import { useMutation } from '@tanstack/react-query'
import { triggerAnalysis } from '../api/client'
import type { AnalysisResult } from '../api/types'

export function useAnalysis(onSuccess?: () => void) {
  const { mutate, isPending, isSuccess, isError, error, data, reset } = useMutation<
    AnalysisResult[],
    Error,
    void
  >({
    mutationFn: () => triggerAnalysis(),
    onSuccess,
  })

  return { mutate, isPending, isSuccess, isError, error, data, reset }
}
