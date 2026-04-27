import { createContext, useContext, useState, useEffect } from "react"
import type { ReactNode } from "react"
import { getCurrentUser, logout as apiLogout } from "@/services/authService"

export interface AuthUser {
  identifier: string
  id: string
  role: string
  firstname: string
  lastname: string
  email: string
  createdAt: string
  langfuse_public_key?: string | null
  langfuse_secret_key_set?: boolean
}

interface AuthContextType {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  refetch: () => Promise<AuthUser | null>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = async (): Promise<AuthUser | null> => {
    try {
      setIsLoading(true)
      setError(null)
      const userData = await getCurrentUser()
      setUser(userData)
      return userData
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch user")
      setUser(null)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  // Check authentication on mount
  useEffect(() => {
    refetch()
  }, [])

  const logout = async () => {
    // Clear user state immediately so route guards react before navigation
    setUser(null)
    setError(null)
    try {
      await apiLogout()
    } catch {
      // Cookie is already gone client-side; ignore API errors
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    refetch,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
