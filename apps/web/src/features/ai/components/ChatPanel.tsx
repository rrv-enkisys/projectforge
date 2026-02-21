import { useState, useRef, useEffect } from 'react'
import { Send, Plus, Trash2, Bot, User, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  useChatSessions,
  useChatMessages,
  useCreateChatSession,
  useDeleteChatSession,
  useSendMessage,
} from '../hooks/useChat'
import type { ChatMessage } from '../hooks/useChat'

interface ChatPanelProps {
  projectId?: string
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? 'bg-blue-600' : 'bg-slate-200'
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-slate-600" />
        )}
      </div>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'bg-blue-600 text-white rounded-tr-sm'
            : 'bg-slate-100 text-slate-800 rounded-tl-sm'
        }`}
      >
        {message.content.split('\n').map((line, i) => (
          <span key={i}>
            {line}
            {i < message.content.split('\n').length - 1 && <br />}
          </span>
        ))}
      </div>
    </div>
  )
}

export function ChatPanel({ projectId }: ChatPanelProps) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { data: sessionsResponse, isLoading: isLoadingSessions } = useChatSessions()
  const { data: messagesResponse, isLoading: isLoadingMessages } = useChatMessages(activeSessionId)
  const createSession = useCreateChatSession()
  const deleteSession = useDeleteChatSession()
  const sendMessage = useSendMessage()

  const sessions = sessionsResponse?.data || []
  const messages = messagesResponse?.data || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleNewSession = async () => {
    try {
      const session = await createSession.mutateAsync({
        title: 'New conversation',
        project_id: projectId,
      })
      setActiveSessionId(session.id)
    } catch {
      toast.error('Failed to create conversation')
    }
  }

  const handleSend = async () => {
    const content = input.trim()
    if (!content || !activeSessionId || isStreaming) return

    setInput('')
    setStreamingContent('')
    setIsStreaming(true)

    try {
      await sendMessage.mutateAsync({
        session_id: activeSessionId,
        content,
        project_id: projectId || null,
      })
    } catch {
      toast.error('Failed to send message')
    } finally {
      setIsStreaming(false)
      setStreamingContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-[600px] overflow-hidden rounded-lg border border-slate-200">
      {/* Sidebar - sessions */}
      <div className="w-56 shrink-0 border-r border-slate-200 bg-slate-50 flex flex-col">
        <div className="p-3 border-b border-slate-200">
          <Button size="sm" className="w-full" onClick={handleNewSession} disabled={createSession.isPending}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            New Chat
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoadingSessions ? (
            [...Array(3)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)
          ) : sessions.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-4">No conversations yet</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                role="button"
                tabIndex={0}
                onClick={() => setActiveSessionId(session.id)}
                onKeyDown={(e) => e.key === 'Enter' && setActiveSessionId(session.id)}
                className={`w-full text-left rounded-md px-3 py-2 text-xs group flex items-center justify-between gap-1 transition-colors cursor-pointer ${
                  activeSessionId === session.id
                    ? 'bg-blue-100 text-blue-800 font-medium'
                    : 'text-slate-600 hover:bg-slate-200'
                }`}
              >
                <span className="truncate">{session.title || 'Conversation'}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteSession.mutate(session.id)
                    if (activeSessionId === session.id) setActiveSessionId(null)
                  }}
                  className="shrink-0 opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-500"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {!activeSessionId ? (
          <div className="flex flex-1 flex-col items-center justify-center text-center p-8 gap-4">
            <Bot className="h-12 w-12 text-slate-300" />
            <div>
              <p className="font-semibold text-slate-700">Start a conversation</p>
              <p className="text-sm text-slate-500 mt-1">
                {projectId
                  ? 'Ask questions about this project and its documents'
                  : 'Create a new chat to get started'}
              </p>
            </div>
            <Button onClick={handleNewSession}>
              <Plus className="mr-2 h-4 w-4" />
              New Conversation
            </Button>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {isLoadingMessages ? (
                [...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-3/4" />)
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                  <Bot className="h-8 w-8 text-slate-300" />
                  <p className="text-sm text-slate-500">
                    {projectId
                      ? 'Ask anything about this project — I have access to project data and documents'
                      : 'How can I help you today?'}
                  </p>
                </div>
              ) : (
                messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
              )}

              {/* Streaming indicator */}
              {isStreaming && (
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200">
                    <Bot className="h-4 w-4 text-slate-600" />
                  </div>
                  <div className="flex items-center gap-1.5 bg-slate-100 rounded-2xl rounded-tl-sm px-4 py-3">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-500" />
                    <span className="text-sm text-slate-500">Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-slate-200 p-3">
              <div className="flex items-end gap-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
                  rows={2}
                  className="flex-1 resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Button
                  size="icon"
                  onClick={handleSend}
                  disabled={!input.trim() || isStreaming || sendMessage.isPending}
                >
                  {isStreaming || sendMessage.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
