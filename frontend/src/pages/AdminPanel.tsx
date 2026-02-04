import { useNavigate } from "react-router-dom";
import { ArrowLeft, Users, Database, Activity } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

export default function AdminPanel() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4 border-b pb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/main-menu")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-primary">System Administration</h1>
          <p className="text-muted-foreground">Manage users, containers, and system health.</p>
        </div>
      </div>

      {/* Admin Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:border-primary/50 cursor-pointer transition-all">
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 bg-chart-2/20 rounded-lg text-chart-2"><Users className="h-6 w-6" /></div>
            <CardTitle>User Management</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Manage roles, approve signups, and block users.</p>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 cursor-pointer transition-all">
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 bg-chart-1/20 rounded-lg text-chart-1"><Database className="h-6 w-6" /></div>
            <CardTitle>Docker Containers</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Monitor up-time and restart services.</p>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 cursor-pointer transition-all">
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="p-2 bg-chart-3/20 rounded-lg text-chart-3"><Activity className="h-6 w-6" /></div>
            <CardTitle>System Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">View application telemetry and error logs.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}