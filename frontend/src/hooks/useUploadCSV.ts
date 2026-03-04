import { useMutation } from '@tanstack/react-query'
import { uploadCSV } from '../api/client'
import type { OperationalRecord } from '../api/types'

export function useUploadCSV() {
  const { mutate, isPending, isSuccess, isError, error, data, reset } = useMutation<
    OperationalRecord[],
    Error,
    File
  >({
    mutationFn: (file: File) => uploadCSV(file),
  })

  return { mutate, isPending, isSuccess, isError, error, data, reset }
}
