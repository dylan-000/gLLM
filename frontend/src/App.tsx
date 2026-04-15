import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import Login from "./pages/Login"
import Signup from "./pages/Signup"
import MainMenu from "./pages/MainMenu"
import AdminPanel from "./pages/AdminPanel"
import RetiredAccess from "./pages/RetiredAccess"
import RequestFinetune from "./pages/RequestFineTune"
import { AuthProvider, useAuth } from "./contexts/AuthContext"
import { UserRole } from "./models/User"

// Loading screen while checking authentication
function LoadingScreen() {
  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  )
}

// Protected route that redirects to login if not authenticated
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Redirect retired users to their specific page
  if (user?.role === UserRole.RETIREDUSER) {
    return <Navigate to="/retired-access" replace />
  }

  return children
}

// Route that redirects to main menu if already authenticated
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  if (isAuthenticated) {
    return <Navigate to="/main-menu" replace />
  }

  return children
}

// Admin-only route
function AdminRoute() {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== UserRole.ADMIN) {
    return <Navigate to="/main-menu" replace />
  }

  return <AdminPanel />
}

function AppRoutes() {
  return (
    <Routes>
      {/* Root redirects to login or main-menu depending on auth */}
      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />

      {/* Public auth routes - redirect to main-menu if already logged in */}
      <Route
        path="/login"
        element={
          <AuthRoute>
            <Login />
          </AuthRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <AuthRoute>
            <Signup />
          </AuthRoute>
        }
      />

      {/* Retired access - public for now */}
      <Route path="/retired-access" element={<RetiredAccess />} />

      {/* Protected routes */}
      <Route
        path="/main-menu"
        element={
          <ProtectedRoute>
            <MainMenu />
          </ProtectedRoute>
        }
      />

      {/* Request access - allow unauthenticated */}
      <Route path="/request-access" element={<RequestFinetune />} />

      {/* Admin-only route */}
      <Route path="/admin" element={<AdminRoute />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}
