import { ShieldAlert } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useNavigate } from "react-router-dom";

export default function RetiredAccess() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md border-destructive/50 shadow-lg">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-4 p-3 rounded-full bg-destructive/10 w-fit">
            <ShieldAlert className="h-10 w-10 text-destructive" />
          </div>
          <CardTitle className="text-2xl text-destructive">Account Suspended</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-center">
          <p className="text-muted-foreground">
            Your account has been retired and is no longer active. You do not have permission to access the gLLM system.
          </p>
          <div className="pt-4 border-t">
            <p className="text-sm text-muted-foreground mb-4">
              If you believe this is an error, please contact system administration.
            </p>
            <Button variant="outline" className="w-full" onClick={() => navigate("/login")}>
              Return to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}