import { Link, useLocation } from 'react-router-dom'
import { Home, FolderKanban, Users, FileText, Settings, ChevronLeft, CheckSquare, Target, Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/stores/uiStore'
import { Button } from '@/components/ui/button'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Tasks', href: '/tasks', icon: CheckSquare },
  { name: 'Milestones', href: '/milestones', icon: Target },
  { name: 'Clients', href: '/clients', icon: Users },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'AI Chat', href: '/chat', icon: Bot },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  const { sidebarOpen, toggleSidebar } = useUIStore()

  return (
    <>
      {/* Sidebar for desktop */}
      <div
        className={cn(
          'hidden md:flex md:flex-col md:fixed md:inset-y-0 z-50 transition-all duration-300',
          sidebarOpen ? 'md:w-64' : 'md:w-16'
        )}
      >
        <div className="flex flex-col flex-grow bg-slate-900 overflow-y-auto">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800">
            {sidebarOpen && (
              <Link to="/dashboard" className="flex items-center">
                <span className="text-xl font-bold text-white">ProjectForge</span>
              </Link>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <ChevronLeft className={cn('h-5 w-5 transition-transform', !sidebarOpen && 'rotate-180')} />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || location.pathname.startsWith(`${item.href}/`)
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                    !sidebarOpen && 'justify-center'
                  )}
                  title={!sidebarOpen ? item.name : undefined}
                >
                  <item.icon className={cn('h-5 w-5 flex-shrink-0', sidebarOpen && 'mr-3')} />
                  {sidebarOpen && <span>{item.name}</span>}
                </Link>
              )
            })}
          </nav>
        </div>
      </div>
    </>
  )
}
