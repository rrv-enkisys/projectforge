import { useState } from 'react'
import { useRAGQuery } from '../hooks/useRAG'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FileText, Search, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DocumentQAPanelProps {
  projectId: string
}

const confidenceColor = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-slate-100 text-slate-600',
}

export function DocumentQAPanel({ projectId }: DocumentQAPanelProps) {
  const [query, setQuery] = useState('')
  const ragQuery = useRAGQuery()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    ragQuery.mutate({ project_id: projectId, question: query.trim() })
  }

  const result = ragQuery.data

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4 text-blue-600" />
          Document Q&A
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={ragQuery.isPending}
            className="text-sm"
          />
          <Button type="submit" size="icon" disabled={ragQuery.isPending || !query.trim()}>
            {ragQuery.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </Button>
        </form>

        {ragQuery.isError && (
          <p className="text-sm text-red-500">
            Error querying documents. Make sure documents are processed.
          </p>
        )}

        {result && (
          <div className="space-y-3">
            {/* Answer */}
            <div className="rounded-lg bg-blue-50 border border-blue-100 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-blue-700 uppercase tracking-wide">Answer</span>
                <span
                  className={cn(
                    'rounded-full px-2 py-0.5 text-xs font-medium',
                    confidenceColor[result.confidence],
                  )}
                >
                  {result.confidence} confidence
                </span>
              </div>
              <p className="text-sm text-slate-800 leading-relaxed">{result.answer}</p>
            </div>

            {/* Sources */}
            {result.sources.length > 0 && (
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
                  Sources ({result.chunks_retrieved} chunks)
                </p>
                <div className="space-y-2">
                  {result.sources.map((source, i) => (
                    <div
                      key={i}
                      className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-slate-700">Chunk #{source.chunk_index + 1}</span>
                        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
                          {(source.similarity * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-slate-600 line-clamp-3 leading-relaxed">{source.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!result && !ragQuery.isPending && (
          <p className="text-xs text-slate-400 text-center py-4">
            Ask a question to search across all processed documents in this project.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
