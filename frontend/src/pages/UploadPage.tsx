import { useRef, useState, useCallback } from 'react'
import { useUploadCSV } from '../hooks/useUploadCSV'
import { ApiError } from '../api/types'

export default function UploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const { mutate, isPending, isSuccess, isError, error, data, reset } = useUploadCSV()

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  function handleSubmit() {
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
    <div className="max-w-[600px] py-8">
      <h1 className="text-[22px] font-bold text-text-primary tracking-tight mb-1">Upload CSV</h1>
      <p className="text-[13.5px] text-text-muted mb-6">Import operational records from a CSV file.</p>

      {/* Drag zone — shown when no file selected */}
      {!selectedFile && !isSuccess && (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={[
            'border-2 border-dashed rounded-xl p-14 text-center cursor-pointer transition-all duration-200 bg-surface',
            dragOver
              ? 'border-border-accent bg-[rgba(6,182,212,0.03)]'
              : 'border-white/[8%] hover:border-border-accent hover:bg-[rgba(6,182,212,0.03)]',
          ].join(' ')}
        >
          <div className="w-[52px] h-[52px] rounded-[14px] bg-primary-glow text-primary-light flex items-center justify-center mx-auto mb-4">
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <h3 className="text-[15px] font-semibold text-text-primary mb-1">Drop your CSV file here</h3>
          <p className="text-[13px] text-text-muted">
            or <span className="text-primary-light font-semibold">browse</span> to choose a file
          </p>
          <p className="text-[11px] text-text-faint mt-3">.csv files only</p>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        disabled={isPending}
        className="hidden"
      />

      {/* File selected — show file row */}
      {selectedFile && !isSuccess && (
        <div className="flex items-center gap-3.5 p-4 rounded-xl bg-surface border border-border">
          <div className="w-[42px] h-[42px] rounded-[10px] bg-primary-glow text-primary-light flex items-center justify-center flex-shrink-0">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-semibold text-text-primary truncate">{selectedFile.name}</p>
            <p className="text-[11px] text-text-faint">{(selectedFile.size / 1024).toFixed(0)} KB</p>
          </div>
          <button
            onClick={handleSubmit}
            disabled={isPending}
            className="inline-flex items-center px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-linear-135/srgb from-primary to-secondary shadow-glow hover:shadow-glow-hover transition-shadow disabled:opacity-35 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {isPending ? 'Uploading...' : 'Upload'}
          </button>
          <button
            onClick={handleReset}
            disabled={isPending}
            className="inline-flex items-center px-4 py-2 bg-surface border border-border text-sm font-medium rounded-lg text-text-secondary hover:bg-surface-hover hover:border-border-hover transition-colors disabled:opacity-50"
          >
            Remove
          </button>
        </div>
      )}

      {isPending && (
        <div className="mt-4 flex items-center gap-2 text-text-secondary">
          <svg className="animate-spin h-5 w-5 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Uploading, please wait...</span>
        </div>
      )}

      {isSuccess && data && (
        <div className="mt-4 rounded-lg bg-success-bg border border-success-border p-4 flex items-start gap-2.5">
          <svg className="h-[18px] w-[18px] text-success flex-shrink-0 mt-px" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="text-success font-semibold text-[13px]">
              Successfully ingested {data.length} record{data.length !== 1 ? 's' : ''}.
            </p>
            <p className="text-[12px] text-success/80 mt-0.5">Records are now available for analysis.</p>
          </div>
        </div>
      )}

      {(isSuccess || isError) && (
        <button
          onClick={handleReset}
          className="mt-3 inline-flex items-center px-4 py-2 bg-surface border border-border text-sm font-medium rounded-lg text-text-secondary hover:bg-surface-hover hover:border-border-hover transition-colors"
        >
          Upload another file
        </button>
      )}

      {isError && apiError && (
        <div className="mt-4">
          {apiError.status === 422 && apiError.errors && apiError.errors.length > 0 ? (
            <div className="rounded-lg bg-danger-bg border border-danger-border p-4">
              <h2 className="text-danger font-semibold mb-3">Validation Errors</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm text-left">
                  <thead>
                    <tr className="border-b border-danger-border">
                      <th className="py-2 pr-4 font-medium text-danger">Row</th>
                      <th className="py-2 pr-4 font-medium text-danger">Field</th>
                      <th className="py-2 font-medium text-danger">Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiError.errors.map((err, idx) => (
                      <tr key={idx} className="border-b border-danger-bg last:border-0">
                        <td className="py-2 pr-4 text-danger">{err.row}</td>
                        <td className="py-2 pr-4 text-danger">{err.field}</td>
                        <td className="py-2 text-danger">{err.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : apiError.status === 413 ? (
            <div className="rounded-lg bg-danger-bg border border-danger-border p-4">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-danger mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-danger">File exceeds the maximum allowed upload size</p>
              </div>
            </div>
          ) : (
            <div className="rounded-lg bg-danger-bg border border-danger-border p-4">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 text-danger mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.294a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-danger">{apiError.message}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
