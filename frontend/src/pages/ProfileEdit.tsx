import { useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { CheckCircle2, ArrowLeft } from "lucide-react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/ui/Logo"
import { cn } from "@/lib/utils"
import { updateProfile } from "@/services/authService"
import { useAuth } from "@/contexts/AuthContext"

export default function ProfileEdit() {
  const navigate = useNavigate();
  const { user, refetch } = useAuth();

  const [submitted, setSubmitted] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    if (user) {
      setFirstName(user.firstname || "")
      setLastName(user.lastname || "")
      setUsername(user.identifier || "")
      setEmail(user.email || "")
    }
  }, [user])

  // Password confirmation logic
  // Only check match if at least one field has text
  const isEditingPassword = password.length > 0 || confirmPassword.length > 0
  const passwordsMatch = isEditingPassword ? password === confirmPassword : true
  const passwordsDontMatch = isEditingPassword ? !passwordsMatch : false

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!passwordsMatch) {
      setError("Passwords do not match")
      return
    }

    setError("")
    setIsLoading(true)

    try {
      await updateProfile({
        identifier: username,
        firstname: firstName,
        lastname: lastName,
        email: email,
        password: password || undefined,
      })
      await refetch()
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profile update failed")
      setIsLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6 font-sans">
        <Card className="max-w-md w-full border-border shadow-lg animate-in fade-in zoom-in duration-300">
          <CardContent className="pt-10 pb-10 text-center space-y-6">
            <div className="mx-auto w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
              <CheckCircle2 className="h-10 w-10 text-primary" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">Profile Updated</h2>
              <p className="text-muted-foreground">
                Your profile information has been successfully updated.
              </p>
            </div>
            <Button onClick={() => navigate("/main-menu")} className="w-full">
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center px-4 font-sans">
      <div className="w-full max-w-md space-y-6 my-10">
        
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-2">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>

        <div className="flex justify-center">
          <Logo />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Edit Profile</CardTitle>
            <CardDescription>Update your account details below.</CardDescription>
          </CardHeader>

          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              {/* Error Message */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/50 text-destructive text-sm p-3 rounded-md">
                  {error}
                </div>
              )}

              {/* Name */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    autoComplete="given-name"
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    autoComplete="family-name"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">New Password (optional)</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  disabled={isLoading}
                  placeholder="Leave blank to keep current password"
                />
              </div>

              {isEditingPassword && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={cn(
                      passwordsDontMatch && "border-destructive focus-visible:ring-destructive",
                      passwordsMatch && "border-green-500 focus-visible:ring-green-500"
                    )}
                    required={isEditingPassword}
                    autoComplete="new-password"
                    disabled={isLoading}
                  />
                </div>
              )}

              {/* LIVE FEEDBACK */}
              {passwordsDontMatch && (
                <p className="text-sm text-destructive">Passwords do not match</p>
              )}
              {isEditingPassword && passwordsMatch && (
                <p className="text-sm text-green-600">Passwords match ✔</p>
              )}

              <Button 
                type="submit" 
                className="w-full" 
                disabled={!passwordsMatch || isLoading}
              >
                {isLoading ? "Saving..." : "Save Changes"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
