# ProjectForge Web App

Modern React + TypeScript frontend for ProjectForge with Firebase authentication.

## Features

- **Firebase Authentication**: Google Sign-In and Email/Password auth
- **Modern UI**: TailwindCSS + shadcn/ui components
- **State Management**: Zustand for client state
- **Data Fetching**: TanStack Query (React Query) for server state
- **Routing**: React Router v6 with protected routes
- **API Integration**: Axios client with automatic token refresh

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS
- **shadcn/ui** - Accessible component library
- **Firebase** - Authentication
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **React Router** - Routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Project Structure

```
src/
├── components/
│   ├── layout/              # Layout components
│   │   ├── AppLayout.tsx    # Main app layout with sidebar
│   │   ├── AuthLayout.tsx   # Auth pages layout
│   │   ├── Header.tsx       # App header with user menu
│   │   └── Sidebar.tsx      # Navigation sidebar
│   ├── ui/                  # Reusable UI components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── avatar.tsx
│   │   ├── dropdown-menu.tsx
│   │   └── skeleton.tsx
│   └── ProtectedRoute.tsx   # Route protection HOC
├── contexts/
│   └── AuthContext.tsx      # Firebase auth context
├── features/
│   └── projects/            # Project feature
│       ├── components/
│       │   └── ProjectCard.tsx
│       ├── hooks/
│       │   └── useProjects.ts
│       └── types.ts
├── lib/
│   ├── api.ts              # Axios instance with interceptors
│   ├── firebase.ts         # Firebase configuration
│   └── utils.ts            # Utility functions
├── pages/
│   ├── LoginPage.tsx       # Login page
│   ├── SignupPage.tsx      # Signup page
│   ├── DashboardPage.tsx   # Dashboard
│   ├── ProjectsPage.tsx    # Projects list
│   ├── ProjectDetailPage.tsx # Project detail with tabs
│   └── NotFoundPage.tsx    # 404 page
├── stores/
│   ├── authStore.ts        # Auth state store
│   └── uiStore.ts          # UI state store
├── styles/
│   └── index.css           # Global styles + Tailwind
├── App.tsx                 # Main app component
└── main.tsx                # Entry point
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm
- Firebase project with Authentication enabled

### Installation

1. Install dependencies:

```bash
npm install
# or
pnpm install
```

2. Configure environment variables:

```bash
cp .env.example .env
```

Update `.env` with your Firebase configuration:

```env
VITE_API_URL=http://localhost:8080
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

3. Start development server:

```bash
npm run dev
# or
pnpm dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
# or
pnpm build
```

### Preview Production Build

```bash
npm run preview
# or
pnpm preview
```

## Authentication Flow

1. User visits the app
2. `AuthProvider` initializes and listens to Firebase auth state
3. `ProtectedRoute` checks if user is authenticated
4. If not authenticated, redirect to `/login`
5. User signs in with Google or Email/Password
6. `AuthContext` updates user state
7. User is redirected to `/dashboard`
8. API calls automatically include Bearer token via axios interceptor

## API Integration

The app uses Axios with interceptors for API calls:

### Request Interceptor
- Automatically adds Firebase ID token to `Authorization` header
- Token is refreshed automatically by Firebase SDK

### Response Interceptor
- Handles 401 errors by signing out user and redirecting to login

### Usage

```typescript
import { api } from '@/lib/api'

// GET request
const response = await api.get('/api/v1/projects')

// POST request
const response = await api.post('/api/v1/projects', {
  name: 'New Project',
  description: 'Project description'
})
```

## State Management

### Auth State (Zustand)
- User authentication state
- Loading state
- Managed by `useAuthStore`

### UI State (Zustand)
- Sidebar open/closed
- Theme preference
- Managed by `useUIStore`
- Persisted to localStorage

### Server State (TanStack Query)
- API data fetching and caching
- Automatic refetching
- Loading and error states

## Component Library

Uses shadcn/ui components built on Radix UI primitives:

- Fully accessible
- Customizable with Tailwind
- Type-safe
- Dark mode ready

## Color Scheme

Primary colors:
- **Backgrounds**: Slate (50-100)
- **Accents**: Blue (500-600)
- **Text**: Slate (600-900)
- **Sidebar**: Slate (900)

## Available Routes

### Public Routes
- `/login` - Login page
- `/signup` - Signup page

### Protected Routes
- `/dashboard` - Dashboard overview
- `/projects` - Projects list
- `/projects/:id` - Project detail
- `/clients` - Clients list (coming soon)
- `/documents` - Documents (coming soon)
- `/settings` - Settings (coming soon)

### Special Routes
- `/` - Redirects to `/dashboard`
- `*` - 404 page

## Development Guidelines

1. **Components**: Create reusable components in `components/ui`
2. **Features**: Group feature-specific code in `features/[feature-name]`
3. **Pages**: Page components in `pages/`
4. **Hooks**: Custom hooks in feature folders or shared `hooks/`
5. **Types**: TypeScript types in feature `types.ts` or shared `types/`
6. **Styles**: Use Tailwind utility classes, avoid custom CSS

## Docker

Build and run with Docker:

```bash
docker build -t projectforge/web .
docker run -p 3000:80 projectforge/web
```

## License

Private - All rights reserved
