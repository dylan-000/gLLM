import { Link, useNavigate } from "react-router-dom"
import { useState, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/ui/Logo"
import { login } from "@/services/authService"
import { useAuth } from "@/contexts/AuthContext"

export default function Login() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const usernameRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const { refetch } = useAuth()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const username = usernameRef.current?.value
      const password = passwordRef.current?.value

      if (!username || !password) {
        setError("Username and password are required")
        setIsLoading(false)
        return
      }

      await login({ username, password })
      // Cookie is automatically set by the server
      // Refetch user data to update auth context
      await refetch()
      // Navigate to main menu on success
      navigate("/main-menu")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex justify-center">
          <Logo />
        </div>

        <Card className="border-border">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Use your username and password.</CardDescription>
          </CardHeader>

          <CardContent>
            <form className="space-y-4" onSubmit={handleLogin}>
              {/* Error Message */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/50 text-destructive text-sm p-3 rounded-md">
                  {error}
                </div>
              )}

              {/* Username */}
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  ref={usernameRef}
                  placeholder="username"
                  autoComplete="username"
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Password with Show/Hide */}
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    ref={passwordRef}
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground hover:text-foreground disabled:opacity-50"
                    disabled={isLoading}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign in"}
              </Button>

              <div className="text-sm text-muted-foreground text-center">
                Don’t have an account?{" "}
                <Link to="/signup" className="text-primary hover:underline">
                  Sign up
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
