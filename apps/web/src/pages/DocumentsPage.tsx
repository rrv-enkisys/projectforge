import { useState, useRef } from 'react'
import { FileText, Upload, Trash2, Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useDocuments, useUploadDocument, useDeleteDocument } from '@/features/documents/hooks/useDocuments'
import type { Document } from '@/features/documents/hooks/useDocuments'

const statusIcon: Record<Document['status'], React.ReactNode> = {
  pending: <Clock className="h-4 w-4 text-slate-400" />,
  processing: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
  processed: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <AlertCircle className="h-4 w-4 text-red-500" />,
}

const statusLabel: Record<Document['status'], string> = {
  pending: 'Queued',
  processing: 'Processing',
  processed: 'Ready',
  failed: 'Failed',
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function DocumentsPage() {
  const { data: response, isLoading } = useDocuments()
  const uploadDocument = useUploadDocument()
  const deleteDocument = useDeleteDocument()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const documents = response?.data || []

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Reset input
    e.target.value = ''

    try {
      await uploadDocument.mutateAsync({
        file,
        projectId: '', // no specific project from this global page
        name: file.name.replace(/\.[^/.]+$/, ''),
      })
      toast.success(`"${file.name}" uploaded successfully`)
    } catch {
      toast.error('Failed to upload document')
    }
  }

  const handleDelete = async (doc: Document) => {
    setDeletingId(doc.id)
    try {
      await deleteDocument.mutateAsync(doc.id)
      toast.success(`"${doc.name}" deleted`)
    } catch {
      toast.error('Failed to delete document')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Documents</h1>
            <p className="mt-1 text-sm text-slate-500">
              Upload documents to enable AI-powered Q&A on your projects
            </p>
          </div>
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploadDocument.isPending}>
            {uploadDocument.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            Upload Document
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx,.txt,.md"
            onChange={handleFileChange}
          />
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 py-16 text-center">
            <FileText className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-semibold text-slate-700">No documents yet</h3>
            <p className="mt-2 text-sm text-slate-500 max-w-sm">
              Upload PDF, Word, or text files to make them searchable by the AI assistant
            </p>
            <Button className="mt-6" onClick={() => fileInputRef.current?.click()}>
              <Upload className="mr-2 h-4 w-4" />
              Upload your first document
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {documents.map((doc) => (
              <Card key={doc.id} className="group hover:shadow-md transition-shadow">
                <CardContent className="pt-5">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
                      <FileText className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-900 truncate">{doc.name}</p>
                      <p className="text-xs text-slate-500">{doc.file_name}</p>
                      <div className="mt-2 flex items-center gap-2">
                        {statusIcon[doc.status]}
                        <span className="text-xs text-slate-600">{statusLabel[doc.status]}</span>
                        <span className="text-xs text-slate-400">·</span>
                        <span className="text-xs text-slate-400">{formatBytes(doc.file_size)}</span>
                        {doc.chunk_count > 0 && (
                          <>
                            <span className="text-xs text-slate-400">·</span>
                            <span className="text-xs text-slate-400">{doc.chunk_count} chunks</span>
                          </>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(doc)}
                      disabled={deletingId === doc.id}
                      className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-500"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
