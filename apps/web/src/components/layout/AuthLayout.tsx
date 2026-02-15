import { ReactNode } from 'react'

interface AuthLayoutProps {
  children: ReactNode
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-900">ProjectForge</h1>
          <p className="mt-2 text-sm text-slate-600">Manage your projects with ease</p>
        </div>

        {/* Auth form card */}
        <div className="bg-white rounded-lg shadow-lg p-8">{children}</div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-slate-500">
          © 2024 ProjectForge. All rights reserved.
        </p>
      </div>
    </div>
  )
}
