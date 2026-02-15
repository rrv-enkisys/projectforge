import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useProject } from '@/features/projects/hooks/useProjects'
import { cn } from '@/lib/utils'

const tabs = [
  { id: 'overview', name: 'Overview' },
  { id: 'tasks', name: 'Tasks' },
  { id: 'documents', name: 'Documents' },
]

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState('overview')
  const { data: project, isLoading, error } = useProject(id!)

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
          <nav className="-mb-px flex space-x-8">
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
        <div className="mt-6">
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
                  <CardTitle>Activity</CardTitle>
                  <CardDescription>Recent project updates</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-500">No recent activity</p>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'tasks' && (
            <Card>
              <CardHeader>
                <CardTitle>Tasks</CardTitle>
                <CardDescription>Manage project tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-500">Task management coming soon...</p>
              </CardContent>
            </Card>
          )}

          {activeTab === 'documents' && (
            <Card>
              <CardHeader>
                <CardTitle>Documents</CardTitle>
                <CardDescription>Project documentation and files</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-500">Document management coming soon...</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
