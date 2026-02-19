import { AppLayout } from '@/components/layout/AppLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <AppLayout>
      <div className="space-y-6 max-w-2xl">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
          <p className="mt-1 text-sm text-slate-500">Manage your account and preferences</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-slate-500">Display Name</p>
              <p className="mt-1 text-sm text-slate-900">{user?.displayName || 'Not set'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Email</p>
              <p className="mt-1 text-sm text-slate-900">{user?.email}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500">Account ID</p>
              <p className="mt-1 text-xs text-slate-400 font-mono">{user?.uid}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>Configure how you receive notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500">
              Notification preferences are managed at the organization level.
              Contact your administrator to update notification settings.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API & Integrations</CardTitle>
            <CardDescription>Connect external services</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <div>
                <p className="text-sm font-medium text-slate-900">Slack</p>
                <p className="text-xs text-slate-500">Receive notifications in Slack</p>
              </div>
              <span className="text-xs text-slate-400">Coming soon</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <div>
                <p className="text-sm font-medium text-slate-900">Webhooks</p>
                <p className="text-xs text-slate-500">Send events to external systems</p>
              </div>
              <span className="text-xs text-slate-400">Available via API</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-slate-900">Email</p>
                <p className="text-xs text-slate-500">Email notifications via Resend</p>
              </div>
              <span className="text-xs text-green-600 font-medium">Active</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
