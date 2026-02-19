import { useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import {
  Trash2, Upload, FileText, Loader2, CheckCircle, AlertCircle,
  Clock, MoreVertical, Plus,
} from 'lucide-react'
import { toast } from 'sonner'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useProject } from '@/features/projects/hooks/useProjects'
import { useTasks, useDeleteTask } from '@/features/tasks/hooks/useTasks'
import { useDocuments, useUploadDocument, useDeleteDocument } from '@/features/documents/hooks/useDocuments'
import { TaskFormDialog } from '@/features/tasks/components/TaskFormDialog'
import { CopilotPanel } from '@/features/ai/components/CopilotPanel'
import { ChatPanel } from '@/features/ai/components/ChatPanel'
import { cn } from '@/lib/utils'
import type { Task } from '@/features/tasks/hooks/useTasks'
import type { Document } from '@/features/documents/hooks/useDocuments'

const tabs = [
  { id: 'overview', name: 'Overview' },
  { id: 'tasks', name: 'Tasks' },
  { id: 'documents', name: 'Documents' },
  { id: 'copilot', name: 'AI Copilot' },
  { id: 'chat', name: 'AI Chat' },
]

const taskStatusColors: Record<Task['status'], string> = {
  todo: 'bg-slate-100 text-slate-700',
  in_progress: 'bg-blue-100 text-blue-700',
  done: 'bg-green-100 text-green-700',
}

const taskPriorityColors: Record<Task['priority'], string> = {
  critical: 'text-red-600',
  high: 'text-orange-600',
  medium: 'text-yellow-600',
  low: 'text-slate-500',
}

const docStatusIcon: Record<Document['status'], React.ReactNode> = {
  pending: <Clock className="h-3.5 w-3.5 text-slate-400" />,
  processing: <Loader2 className="h-3.5 w-3.5 text-blue-500 animate-spin" />,
  processed: <CheckCircle className="h-3.5 w-3.5 text-green-500" />,
  failed: <AlertCircle className="h-3.5 w-3.5 text-red-500" />,
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState('overview')
  const [deletingTaskId, setDeletingTaskId] = useState<string | null>(null)
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: project, isLoading, error } = useProject(id!)
  const { data: tasksResponse } = useTasks(id)
  const { data: docsResponse } = useDocuments(id)
  const deleteTask = useDeleteTask()
  const uploadDocument = useUploadDocument()
  const deleteDocument = useDeleteDocument()

  const tasks = tasksResponse?.data || []
  const documents = docsResponse?.data || []

  const handleDeleteTask = async (taskId: string) => {
    setDeletingTaskId(taskId)
    try {
      await deleteTask.mutateAsync(taskId)
      toast.success('Task deleted')
    } catch {
      toast.error('Failed to delete task')
    } finally {
      setDeletingTaskId(null)
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !id) return
    e.target.value = ''
    try {
      await uploadDocument.mutateAsync({ file, projectId: id })
      toast.success(`"${file.name}" uploaded`)
    } catch {
      toast.error('Failed to upload document')
    }
  }

  const handleDeleteDoc = async (docId: string, name: string) => {
    setDeletingDocId(docId)
    try {
      await deleteDocument.mutateAsync(docId)
      toast.success(`"${name}" deleted`)
    } catch {
      toast.error('Failed to delete document')
    } finally {
      setDeletingDocId(null)
    }
  }

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      </AppLayout>
    )
  }

  if (error || !project) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-red-600">Failed to load project. Please try again.</p>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Project header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{project.name}</h1>
          <p className="mt-2 text-sm text-slate-600">{project.description}</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-200">
          <nav className="-mb-px flex space-x-6 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                )}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div>
          {/* Overview */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Project Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Status</p>
                    <p className="mt-1 text-sm text-slate-900 capitalize">{project.status.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-500">Start Date</p>
                    <p className="mt-1 text-sm text-slate-900">
                      {new Date(project.start_date).toLocaleDateString()}
                    </p>
                  </div>
                  {project.end_date && (
                    <div>
                      <p className="text-sm font-medium text-slate-500">End Date</p>
                      <p className="mt-1 text-sm text-slate-900">
                        {new Date(project.end_date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                  {project.budget && (
                    <div>
                      <p className="text-sm font-medium text-slate-500">Budget</p>
                      <p className="mt-1 text-sm text-slate-900">${project.budget.toLocaleString()}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Summary</CardTitle>
                  <CardDescription>Quick project stats</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-slate-50 p-3 text-center">
                    <p className="text-2xl font-bold text-slate-900">{tasks.length}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Total Tasks</p>
                  </div>
                  <div className="rounded-lg bg-green-50 p-3 text-center">
                    <p className="text-2xl font-bold text-green-700">
                      {tasks.filter((t) => t.status === 'done').length}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">Completed</p>
                  </div>
                  <div className="rounded-lg bg-blue-50 p-3 text-center">
                    <p className="text-2xl font-bold text-blue-700">
                      {tasks.filter((t) => t.status === 'in_progress').length}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">In Progress</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3 text-center">
                    <p className="text-2xl font-bold text-slate-700">{documents.length}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Documents</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tasks */}
          {activeTab === 'tasks' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{tasks.length} task{tasks.length !== 1 ? 's' : ''}</p>
                <TaskFormDialog defaultProjectId={id} />
              </div>

              {tasks.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center py-12 gap-4">
                    <p className="text-slate-500 text-sm">No tasks yet</p>
                    <TaskFormDialog defaultProjectId={id} trigger={
                      <Button variant="outline">
                        <Plus className="mr-2 h-4 w-4" />
                        Add first task
                      </Button>
                    } />
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-2">
                  {tasks.map((task) => (
                    <Card key={task.id} className="group hover:shadow-sm transition-shadow">
                      <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-medium text-slate-900 truncate">{task.title}</p>
                              <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize', taskStatusColors[task.status])}>
                                {task.status.replace('_', ' ')}
                              </span>
                              <span className={cn('text-xs font-medium capitalize', taskPriorityColors[task.priority])}>
                                {task.priority}
                              </span>
                            </div>
                            {task.description && (
                              <p className="text-sm text-slate-500 truncate mt-0.5">{task.description}</p>
                            )}
                            {task.due_date && (
                              <p className="text-xs text-slate-400 mt-1">
                                Due {new Date(task.due_date).toLocaleDateString()}
                              </p>
                            )}
                          </div>

                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <TaskFormDialog task={task} trigger={
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            } />
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleDeleteTask(task.id)}
                              disabled={deletingTaskId === task.id}
                            >
                              {deletingTaskId === task.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Documents */}
          {activeTab === 'documents' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">{documents.length} document{documents.length !== 1 ? 's' : ''}</p>
                <Button onClick={() => fileInputRef.current?.click()} disabled={uploadDocument.isPending}>
                  {uploadDocument.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Upload
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt,.md"
                  onChange={handleFileChange}
                />
              </div>

              {documents.length === 0 ? (
                <div className="flex flex-col items-center rounded-xl border-2 border-dashed border-slate-200 py-12 text-center gap-4">
                  <FileText className="h-10 w-10 text-slate-300" />
                  <div>
                    <p className="font-medium text-slate-700">No documents yet</p>
                    <p className="text-sm text-slate-500 mt-1">Upload files to enable AI Q&A on this project</p>
                  </div>
                  <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload document
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <Card key={doc.id} className="group hover:shadow-sm transition-shadow">
                      <CardContent className="py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
                            <FileText className="h-4 w-4 text-blue-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-slate-900 truncate">{doc.name}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              {docStatusIcon[doc.status]}
                              <span className="text-xs text-slate-500">{formatBytes(doc.file_size)}</span>
                              {doc.chunk_count > 0 && (
                                <span className="text-xs text-slate-400">· {doc.chunk_count} chunks indexed</span>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50"
                            onClick={() => handleDeleteDoc(doc.id, doc.name)}
                            disabled={deletingDocId === doc.id}
                          >
                            {deletingDocId === doc.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AI Copilot */}
          {activeTab === 'copilot' && (
            <CopilotPanel projectId={id!} />
          )}

          {/* AI Chat */}
          {activeTab === 'chat' && (
            <ChatPanel projectId={id} />
          )}
        </div>
      </div>
    </AppLayout>
  )
}
