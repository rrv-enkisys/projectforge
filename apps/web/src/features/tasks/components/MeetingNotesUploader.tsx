import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, Loader2, Upload, X } from 'lucide-react'
import { toast } from 'sonner'
import { useAnalyzeMeetingNotes, type MeetingNotesParseResponse } from '@/features/ai/hooks/useMeetingNotes'
import { ActionItemsReviewPanel } from './ActionItemsReviewPanel'

interface MeetingNotesUploaderProps {
  onDone: () => void
}

const ACCEPTED_TYPES = {
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'text/vtt': ['.vtt'],
  'text/csv': ['.csv'],
}
const MAX_SIZE = 5 * 1024 * 1024

export function MeetingNotesUploader({ onDone }: MeetingNotesUploaderProps) {
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<MeetingNotesParseResponse | null>(null)

  const analyze = useAnalyzeMeetingNotes()

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    multiple: false,
    onDropRejected: (rejections) => {
      const err = rejections[0]?.errors[0]
      if (err?.code === 'file-too-large') {
        toast.error('File exceeds 5 MB limit.')
      } else {
        toast.error('Unsupported file type. Use TXT, MD, VTT, or CSV.')
      }
    },
  })

  const handleAnalyzeFile = async () => {
    if (!file) return
    try {
      const data = await analyze.mutateAsync(file)
      setResult(data)
    } catch {
      toast.error('Failed to analyze file. Please try again.')
    }
  }

  const handleAnalyzeText = async () => {
    if (!text.trim()) return
    try {
      const data = await analyze.mutateAsync(text.trim())
      setResult(data)
    } catch {
      toast.error('Failed to analyze transcript. Please try again.')
    }
  }

  if (result) {
    return <ActionItemsReviewPanel result={result} onDone={onDone} />
  }

  return (
    <Tabs defaultValue="text" className="space-y-4">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="text">Paste transcript</TabsTrigger>
        <TabsTrigger value="file">Upload file</TabsTrigger>
      </TabsList>

      {/* Text tab */}
      <TabsContent value="text" className="space-y-3">
        <Textarea
          placeholder="Paste your meeting transcript here…"
          className="min-h-[220px] resize-none text-sm font-mono"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">{text.length.toLocaleString()} chars</span>
          <Button
            onClick={handleAnalyzeText}
            disabled={!text.trim() || analyze.isPending}
          >
            {analyze.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              'Analyze Transcript'
            )}
          </Button>
        </div>
      </TabsContent>

      {/* File tab */}
      <TabsContent value="file" className="space-y-3">
        {file ? (
          <div className="flex items-center gap-3 p-4 rounded-lg border border-slate-200 bg-slate-50">
            <FileText className="h-8 w-8 text-slate-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
              onClick={() => setFile(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div
            {...getRootProps()}
            className={`flex flex-col items-center justify-center gap-3 p-10 rounded-lg border-2 border-dashed cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className={`h-8 w-8 ${isDragActive ? 'text-blue-400' : 'text-slate-300'}`} />
            <div className="text-center">
              <p className="text-sm font-medium text-slate-700">
                {isDragActive ? 'Drop your file here' : 'Drag & drop or click to upload'}
              </p>
              <p className="text-xs text-slate-500 mt-1">TXT, MD, VTT, CSV — up to 5 MB</p>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <Button
            onClick={handleAnalyzeFile}
            disabled={!file || analyze.isPending}
          >
            {analyze.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              'Analyze File'
            )}
          </Button>
        </div>
      </TabsContent>
    </Tabs>
  )
}
