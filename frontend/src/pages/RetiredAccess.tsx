import { ShieldAlert } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function RetiredAccess() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleReturnToLogin = async () => {
    // Clear the auth cookie and AuthContext user state before navigating.
    // Without this, AuthRoute sees the user as still authenticated and
    // redirects back to /main-menu → /retired-access (an infinite loop).
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md border-destructive/50 shadow-lg">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 p-3 rounded-full bg-destructive/10 w-fit">
            <ShieldAlert className="h-10 w-10 text-destructive" />
          </div>
          <CardTitle className="text-2xl text-destructive">Account Under Review</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-center">
          <p className="text-muted-foreground">
            Your account is currently under review and is not active. You have either just sent a sign-up request or your account was suspended by an administrator.
          </p>
          <div className="pt-4 border-t">
            <p className="text-sm text-muted-foreground mb-4">
              Contact your administrator for confirmation on the status of your account.
            </p>
            <Button variant="outline" className="w-full" onClick={handleReturnToLogin}>
              Return to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}