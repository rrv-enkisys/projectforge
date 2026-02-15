import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FolderKanban, Users, FileText, CheckSquare } from 'lucide-react'

const stats = [
  {
    name: 'Active Projects',
    value: '12',
    icon: FolderKanban,
    change: '+2 from last month',
    changeType: 'positive',
  },
  {
    name: 'Total Clients',
    value: '8',
    icon: Users,
    change: '+1 from last month',
    changeType: 'positive',
  },
  {
    name: 'Documents',
    value: '145',
    icon: FileText,
    change: '+12 from last week',
    changeType: 'positive',
  },
  {
    name: 'Tasks Completed',
    value: '89',
    icon: CheckSquare,
    change: '+23 this week',
    changeType: 'positive',
  },
]

export default function DashboardPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-2 text-sm text-slate-600">
            Welcome back! Here's an overview of your projects and activities.
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.name}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">{stat.name}</CardTitle>
                <stat.icon className="h-4 w-4 text-slate-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
                <p className="text-xs text-slate-500 mt-1">{stat.change}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent activity */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>Your most recently updated projects</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">Website Redesign</p>
                    <p className="text-sm text-slate-500">Updated 2 hours ago</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">Mobile App Development</p>
                    <p className="text-sm text-slate-500">Updated 5 hours ago</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">Brand Guidelines</p>
                    <p className="text-sm text-slate-500">Updated yesterday</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Planning
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Upcoming Tasks</CardTitle>
              <CardDescription>Tasks due in the next 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Complete UI mockups</p>
                    <p className="text-sm text-slate-500">Due in 2 days</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    High
                  </span>
                </div>
                <div className="flex items-start">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Client review meeting</p>
                    <p className="text-sm text-slate-500">Due in 3 days</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Medium
                  </span>
                </div>
                <div className="flex items-start">
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">Update project documentation</p>
                    <p className="text-sm text-slate-500">Due in 5 days</p>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    Low
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
