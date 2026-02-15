import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Home } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-slate-900">404</h1>
        <p className="mt-4 text-2xl font-semibold text-slate-700">Page not found</p>
        <p className="mt-2 text-slate-600">Sorry, we couldn't find the page you're looking for.</p>
        <div className="mt-8">
          <Link to="/dashboard">
            <Button>
              <Home className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
