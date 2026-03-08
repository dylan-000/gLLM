import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import Login from "./pages/Login"
import Signup from "./pages/Signup"
import MainMenu from "./pages/MainMenu";
import AdminPanel from "./pages/AdminPanel";
import RetiredAccess from "./pages/RetiredAccess";
import RequestFinetune from "./pages/RequestFineTune";
import { UserRole } from "./models/User";
import { useAuth } from "./contexts/AuthContext";

export default function App() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (!isAuthenticated || !user) {
      return <Navigate to="/login" replace />;
    }
    if (user.role === UserRole.UNAUTHORIZED) {
      return <Navigate to="/retired-access" replace />;
    }
    return children;
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/main-menu" replace />} />

        <Route path="/login" element={
          isAuthenticated ? <Navigate to="/main-menu" replace /> : <Login />
        } />
        <Route path="/signup" element={
          isAuthenticated ? <Navigate to="/main-menu" replace /> : <Signup />
        } />
        <Route path="/retired-access" element={<RetiredAccess />} />

        <Route
          path="/main-menu"
          element={
            <ProtectedRoute>
              <MainMenu />
            </ProtectedRoute>
          }
        />
        <Route path="/request-access" element={<RequestFinetune />} />

        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              {user?.role === UserRole.ADMIN ? <AdminPanel /> : <Navigate to="/main-menu" />}
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
