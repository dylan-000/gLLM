import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { useEffect, useState } from "react"
import Login from "./pages/Login"
import Signup from "./pages/Signup"
import MainMenu from "./pages/MainMenu";
import AdminPanel from "./pages/AdminPanel";
import RetiredAccess from "./pages/RetiredAccess";
import { UserRole } from "./models/User";

// Test User
const MOCK_USER = {
  isAuthenticated: true,
  role: UserRole.ADMIN 
};

export default function App() {
  const [dark, setDark] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
  }, [dark])

  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    if (!MOCK_USER.isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    // Strict Check for Retired Users
    if (MOCK_USER.role === UserRole.RETIREDUSER) {
      return <Navigate to="/retired-access" replace />;
    }
    return children;
  };

  return (
    <BrowserRouter>
      {/* DARK MODE TOGGLE BUTTON */}
      <button
        onClick={() => setDark((v) => !v)}
        className="fixed top-4 right-4 bg-card border px-3 py-2 rounded-xl shadow-lg z-50"
      >
        {dark ? "🌙 Dark" : "☀️ Light"}
      </button>

      <Routes>
        <Route path="/" element={<Navigate to="/main-menu" replace />} />
        
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/retired-access" element={<RetiredAccess />} />

        <Route
          path="/main-menu"
          element={
            <ProtectedRoute>
              <MainMenu />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              {MOCK_USER.role === UserRole.ADMIN ? <AdminPanel /> : <Navigate to="/main-menu" />}
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
