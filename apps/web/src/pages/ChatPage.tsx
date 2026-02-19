import { AppLayout } from '@/components/layout/AppLayout'
import { ChatPanel } from '@/features/ai/components/ChatPanel'

export default function ChatPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">AI Assistant</h1>
          <p className="mt-1 text-sm text-slate-500">
            Ask questions, get insights, and get help with your projects
          </p>
        </div>
        <ChatPanel />
      </div>
    </AppLayout>
  )
}
