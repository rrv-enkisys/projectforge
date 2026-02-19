import { Bell, Check, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  useNotifications,
  useUnreadCount,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
} from '../hooks/useNotifications'

export function NotificationBell() {
  const { data: notifResponse } = useNotifications(false)
  const { data: unreadCount = 0 } = useUnreadCount()
  const markAsRead = useMarkAsRead()
  const markAllAsRead = useMarkAllAsRead()
  const deleteNotif = useDeleteNotification()

  const notifications = notifResponse?.data?.slice(0, 8) || []

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 max-h-[480px] overflow-y-auto">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <button
              onClick={() => markAllAsRead.mutate()}
              className="text-xs text-blue-600 hover:underline font-normal"
            >
              Mark all read
            </button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {notifications.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500">
            No notifications yet
          </div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              className={`flex items-start gap-2 px-2 py-2 hover:bg-slate-50 group ${
                notif.status === 'pending' ? 'bg-blue-50/50' : ''
              }`}
            >
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${notif.status === 'pending' ? 'font-semibold' : 'font-medium'} truncate`}>
                  {notif.title}
                </p>
                <p className="text-xs text-slate-500 truncate">{notif.body}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}
                </p>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                {notif.status === 'pending' && (
                  <button
                    onClick={() => markAsRead.mutate(notif.id)}
                    className="p-1 rounded hover:bg-slate-200"
                    title="Mark as read"
                  >
                    <Check className="h-3.5 w-3.5 text-blue-600" />
                  </button>
                )}
                <button
                  onClick={() => deleteNotif.mutate(notif.id)}
                  className="p-1 rounded hover:bg-slate-200"
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5 text-red-500" />
                </button>
              </div>
            </div>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
