import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { useEffect, useState } from "react"
import Login from "./pages/Login"
import Signup from "./pages/Signup"

export default function App() {
  const [dark, setDark] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
  }, [dark])

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
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </BrowserRouter>
  )
}
