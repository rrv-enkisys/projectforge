import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useParseSOW } from '@/features/ai/hooks/useSOWParser'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { AlertTriangle, FileText, Loader2, Upload, Wand2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SOWReviewPanel } from './SOWReviewPanel'

interface SOWUploaderProps {
  onProjectCreated?: (projectId: string) => void
}

export function SOWUploader({ onProjectCreated }: SOWUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const parseSOW = useParseSOW()

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0])
        parseSOW.reset()
      }
    },
    [parseSOW],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  })

  const handleReset = () => {
    setFile(null)
    parseSOW.reset()
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="h-5 w-5 text-purple-500" />
          Create Project from SOW
        </CardTitle>
        <CardDescription>
          Upload a Statement of Work and let AI generate your project structure automatically
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Drop zone — always visible so user can swap the file */}
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            isDragActive && 'border-purple-500 bg-purple-50',
            !isDragActive && !file && 'border-slate-200 hover:border-slate-300',
            file && !parseSOW.data && 'border-blue-300 bg-blue-50',
            parseSOW.data && 'border-green-300 bg-green-50',
          )}
        >
          <input {...getInputProps()} />

          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="h-8 w-8 text-blue-500" />
              <div className="text-left">
                <p className="font-medium text-slate-800">{file.name}</p>
                <p className="text-sm text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB · click to change
                </p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="mx-auto h-12 w-12 text-slate-400" />
              <p className="mt-2 text-sm text-slate-600">
                {isDragActive ? 'Drop the file here' : 'Drag & drop your SOW, or click to select'}
              </p>
              <p className="text-xs text-slate-500 mt-1">PDF, DOCX, TXT, or Markdown · max 10 MB</p>
            </>
          )}
        </div>

        {/* Parse button */}
        {file && !parseSOW.data && !parseSOW.isPending && (
          <Button onClick={() => parseSOW.mutate(file)} className="w-full">
            <Wand2 className="mr-2 h-4 w-4" />
            Generate Project Structure
          </Button>
        )}

        {/* Loading state */}
        {parseSOW.isPending && (
          <div className="flex items-center justify-center gap-2 py-2 text-slate-600 text-sm">
            <Loader2 className="h-4 w-4 animate-spin" />
            Analyzing document with AI…
          </div>
        )}

        {/* Error */}
        {parseSOW.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-700">Failed to parse SOW</p>
              <p className="text-sm text-red-600">
                {(parseSOW.error as any)?.response?.data?.detail ||
                  parseSOW.error?.message ||
                  'Please try again'}
              </p>
            </div>
          </div>
        )}

        {/* Review + create panel */}
        {parseSOW.data && (
          <SOWReviewPanel
            result={parseSOW.data}
            onProjectCreated={onProjectCreated}
            onReset={handleReset}
          />
        )}
      </CardContent>
    </Card>
  )
}
