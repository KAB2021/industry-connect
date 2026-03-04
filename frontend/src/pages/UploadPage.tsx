import { useRef, useState } from 'react'
import { useUploadCSV } from '../hooks/useUploadCSV'
import { ApiError } from '../api/types'

export default function UploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { mutate, isPending, isSuccess, isError, error, data, reset } = useUploadCSV()

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedFile) return
    mutate(selectedFile)
  }

  function handleReset() {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    reset()
  }

  const apiError = isError && error instanceof ApiError ? error : null

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Upload CSV</h1>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4">
        <div>
          <label htmlFor="csv-file" className="block text-sm font-medium text-gray-700 mb-1">
            CSV File
          </label>
          <input
            id="csv-file"
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={isPending}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-medium
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={!selectedFile || isPending}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? 'Uploading...' : 'Upload'}
          </button>

          {(isSuccess || isError) && (
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Reset
            </button>
          )}
        </div>
      </form>

      {isPending && (
        <div className="mt-4 flex items-center gap-2 text-gray-600">
          <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Uploading, please wait...</span>
        </div>
      )}

      {isSuccess && data && (
        <div className="mt-4 rounded-md bg-green-50 border border-green-200 p-4">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="text-green-800 font-medium">
              Successfully ingested {data.length} record{data.length !== 1 ? 's' : ''}.
            </p>
          </div>
        </div>
      )}

      {isError && apiError && (
        <div className="mt-4">
          {apiError.status === 422 && apiError.errors && apiError.errors.length > 0 ? (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <h2 className="text-red-800 font-semibold mb-3">Validation Errors</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-left">
                  <thead>
                    <tr className="border-b border-red-200">
                      <th className="py-2 pr-4 font-medium text-red-700">Row</th>
                      <th className="py-2 pr-4 font-medium text-red-700">Field</th>
                      <th className="py-2 font-medium text-red-700">Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiError.errors.map((err, idx) => (
                      <tr key={idx} className="border-b border-red-100 last:border-0">
                        <td className="py-2 pr-4 text-red-900">{err.row}</td>
                        <td className="py-2 pr-4 text-red-900">{err.field}</td>
                        <td className="py-2 text-red-900">{err.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : apiError.status === 413 ? (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-800">File exceeds the maximum allowed upload size</p>
              </div>
            </div>
          ) : (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.294a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-red-800">{apiError.message}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
