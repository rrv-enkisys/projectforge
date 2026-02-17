import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

// DEVELOPMENT MODE: Bypass authentication
const DEV_MODE = import.meta.env.DEV || import.meta.env.MODE === 'development'

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Skip authentication in development mode
  if (DEV_MODE) {
    return <>{children}</>
  }

  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
