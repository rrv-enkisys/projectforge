function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
      <div className="text-center space-y-6 p-8">
        <h1 className="text-6xl font-bold text-white">
          ProjectForge
        </h1>
        <p className="text-xl text-slate-300">
          AI-Powered Project Management Platform
        </p>
        <div className="flex gap-4 justify-center mt-8">
          <span className="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium">
            React + TypeScript
          </span>
          <span className="px-4 py-2 bg-purple-500 text-white rounded-lg font-medium">
            TailwindCSS
          </span>
          <span className="px-4 py-2 bg-green-500 text-white rounded-lg font-medium">
            Vite
          </span>
        </div>
      </div>
    </div>
  )
}

export default HomePage
