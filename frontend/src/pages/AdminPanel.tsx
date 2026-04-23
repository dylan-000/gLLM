import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, Users, Database } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { adminService, type ContainerStatus } from "../services/adminService";

export default function AdminPanel() {
  const navigate = useNavigate();
  const [containerStatus, setContainerStatus] = useState<ContainerStatus | null>(null);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const status = await adminService.getContainerStatus();
      setContainerStatus(status);
    } catch (e) {
      console.error("Failed to fetch container status", e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const intervalId = setInterval(fetchStatus, 10000);
    return () => clearInterval(intervalId);
  }, []);

  const handleStart = async (service: 'vllm' | 'unsloth') => {
    setLoadingAction(`${service}-start`);
    try {
      await adminService.startContainer(service);
      await fetchStatus();
    } catch (e) {
      console.error(e);
    }
    setLoadingAction(null);
  };

  const handleStop = async (service: 'vllm' | 'unsloth') => {
    setLoadingAction(`${service}-stop`);
    try {
      await adminService.stopContainer(service);
      await fetchStatus();
    } catch (e) {
      console.error(e);
    }
    setLoadingAction(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">

      {/* Top Bar (Simplified for Admin View) */}
      <div className="border-b border-border bg-card sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate("/main-menu")}>
              <ArrowLeft className="h-4 w-4 mr-2" /> Back
            </Button>
            <div className="h-6 w-px bg-border mx-2" />
            <h1 className="font-bold text-lg flex items-center gap-2">
              <ShieldIcon className="text-chart-1 h-5 w-5" />
              Admin Console
            </h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <AdminStatCard
            title="Total Users"
            value="3"
            icon={<Users className="h-5 w-5 text-blue-500" />}
          />
          <AdminStatCard
            title="Current Active Containers"
            value="vLLM"
            icon={<Database className="h-5 w-5 text-green-500" />}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* User Management Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold tracking-tight">User Management</h2>
              <Button variant="outline" size="sm">View All</Button>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Pending Approvals</CardTitle>
                <CardDescription>New users requesting access.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold">U{i}</div>
                      <div>
                        <p className="text-sm font-medium">User_{i} Request</p>
                        <p className="text-xs text-muted-foreground">user{i}@example.com</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default" className="h-7 text-xs">Approve</Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs text-destructive hover:bg-destructive/10">Deny</Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold tracking-tight">Model Services</h2>
              <Button variant="outline" size="sm" onClick={fetchStatus}>Refresh</Button>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Containers</CardTitle>
                <CardDescription>Manage your local AI models</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {(['vllm', 'unsloth'] as const).map(service => (
                  <div key={service} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className={`h-3 w-3 rounded-full ${containerStatus?.[service]?.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`} />
                      <div>
                        <p className="text-sm font-medium capitalize">{service}</p>
                        <p className="text-xs text-muted-foreground">Status: {containerStatus?.[service]?.status || 'unknown'}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default" className="h-7 text-xs"
                        disabled={containerStatus?.[service]?.status === 'up' || loadingAction === `${service}-start`}
                        onClick={() => handleStart(service)}
                      >
                        {loadingAction === `${service}-start` ? 'Starting...' : 'Start'}
                      </Button>
                      <Button size="sm" variant="destructive" className="h-7 text-xs"
                        disabled={containerStatus?.[service]?.status === 'down' || loadingAction === `${service}-stop`}
                        onClick={() => handleStop(service)}
                      >
                        {loadingAction === `${service}-stop` ? 'Stopping...' : 'Stop'}
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

      </div>
    </div>
  );
}

function AdminStatCard({ title, value, desc, icon }: any) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {icon}
        </div>
        <div className="flex items-end justify-between mt-2">
          <div className="text-2xl font-bold">{value}</div>
          <p className="text-xs text-muted-foreground">{desc}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function ShieldIcon({ className }: any) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
    </svg>
  )
}