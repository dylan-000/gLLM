import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, Users, Database, X, Trash2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { adminService, type ContainerStatus } from "../services/adminService";

export default function AdminPanel() {
  const navigate = useNavigate();
  const [containerStatus, setContainerStatus] = useState<ContainerStatus | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [showAllUsers, setShowAllUsers] = useState(false);

  const fetchUsers = async () => {
    try {
      const data = await adminService.getUsers();
      setUsers(data);
    } catch (e) {
      console.error("Failed to fetch users", e);
    }
  };

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
    fetchUsers();
    const intervalId = setInterval(() => {
      fetchStatus();
      fetchUsers();
    }, 10000);
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

  const handleRoleChange = async (userId: string, newRole: string) => {
    setLoadingAction(`role-${userId}`);
    try {
      await adminService.updateUserRole(userId, newRole);
      await fetchUsers();
    } catch (e) {
      console.error(e);
    }
    setLoadingAction(null);
  };

  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm("Are you sure you want to remove this user?")) return;
    setLoadingAction(`delete-${userId}`);
    try {
      await adminService.deleteUser(userId);
      await fetchUsers();
    } catch (e) {
      console.error(e);
      alert("Failed to delete user");
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
            value={users.length.toString()}
            icon={<Users className="h-5 w-5 text-blue-500" />}
          />
          <AdminStatCard
            title="Current Active Containers on GPU"
            value={containerStatus?.vllm?.status === 'up' ? 'vLLM' : containerStatus?.unsloth?.status === 'up' ? 'UnSloth' : 'None'}
            icon={<Database className="h-5 w-5 text-green-500" />}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* User Management Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold tracking-tight">User Management</h2>
              <Button variant="outline" size="sm" onClick={() => setShowAllUsers(true)}>
                View All
              </Button>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>User Roles</CardTitle>
                <CardDescription>
                  Manage roles for registered users. 
                  {users.length > 5 && ` Showing 5 of ${users.length} users.`}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {users.slice(0, 5).map((u) => (
                  <div key={u.id} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold uppercase">{u.identifier.substring(0, 2)}</div>
                      <div>
                        <p className="text-sm font-medium">{u.identifier}</p>
                        <p className="text-xs text-muted-foreground">{u.email || 'No email'}</p>
                      </div>
                    </div>
                    <div className="flex gap-2 items-center">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        disabled={loadingAction === `role-${u.id}`}
                        className="text-xs bg-background border border-border rounded p-1"
                      >
                        <option value="unauthorized">Unauthorized</option>
                        <option value="normal">RegUser</option>
                        <option value="fine_tuner">Fine Tuner</option>
                        <option value="admin">Admin</option>
                      </select>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={loadingAction === `delete-${u.id}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
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

      {/* View All Users Modal */}
      {showAllUsers && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border pb-4">
              <div>
                <CardTitle>All Users</CardTitle>
                <CardDescription>Manage all {users.length} registered users.</CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowAllUsers(false)}>
                <X className="h-5 w-5" />
              </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center text-sm font-bold uppercase">{u.identifier.substring(0, 2)}</div>
                    <div>
                      <p className="text-sm font-medium">{u.identifier}</p>
                      <p className="text-xs text-muted-foreground">{u.email || 'No email'} • Joined: {new Date(u.createdAt).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="flex gap-3 items-center">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      disabled={loadingAction === `role-${u.id}`}
                      className="text-sm bg-background border border-border rounded p-2"
                    >
                      <option value="unauthorized">Unauthorized</option>
                      <option value="normal">RegUser</option>
                      <option value="fine_tuner">Fine Tuner</option>
                      <option value="admin">Admin</option>
                    </select>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="h-9 px-3 flex gap-2"
                      onClick={() => handleDeleteUser(u.id)}
                      disabled={loadingAction === `delete-${u.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

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