import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, Users, Activity, Search, CheckCircle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { getUsers, updateUserRole, deleteUser } from "../services/api";
import type { User } from "../models/User";

export default function AdminPanel() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await getUsers();
      setUsers(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const pendingUsers = users.filter((u) => u.role === "unauthorized");
  const activeUsers = users.filter((u) => u.role !== "unauthorized");

  const handleApprove = async (userId: string) => {
    try {
      await updateUserRole(userId, "normal");
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve user");
    }
  };

  const handleDeny = async (userId: string) => {
    try {
      await deleteUser(userId);
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deny user");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">

      {/* Top Bar */}
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
          <div className="flex items-center gap-4">
             <div className="relative hidden md:block">
               <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
               <Input placeholder="Search users..." className="pl-9 w-64 h-9" />
             </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">

        {error && (
          <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 p-3 rounded-md">
            {error}
          </div>
        )}

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <AdminStatCard
            title="Total Users"
            value={String(users.length)}
            desc={`${pendingUsers.length} pending`}
            icon={<Users className="h-5 w-5 text-blue-500" />}
          />
          <AdminStatCard
            title="Active Users"
            value={String(activeUsers.length)}
            desc="Approved accounts"
            icon={<CheckCircle className="h-5 w-5 text-green-500" />}
          />
          <AdminStatCard
            title="Pending Approvals"
            value={String(pendingUsers.length)}
            desc="Awaiting review"
            icon={<Activity className="h-5 w-5 text-orange-500" />}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pending Approvals */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
               <h2 className="text-xl font-semibold tracking-tight">Pending Approvals</h2>
               <Button variant="outline" size="sm" onClick={fetchUsers} disabled={loading}>
                 {loading ? "Loading..." : "Refresh"}
               </Button>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>New User Requests</CardTitle>
                <CardDescription>Users requesting access to the system.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading && <p className="text-sm text-muted-foreground">Loading users...</p>}

                {!loading && pendingUsers.length === 0 && (
                  <p className="text-sm text-muted-foreground">No pending requests.</p>
                )}

                {pendingUsers.map((user) => (
                  <div key={user.id} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold">
                        {user.identifier[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{user.identifier}</p>
                        <p className="text-xs text-muted-foreground">{user.email || "No email"}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="default" className="h-7 text-xs" onClick={() => handleApprove(user.id)}>
                        Approve
                      </Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs text-destructive hover:bg-destructive/10" onClick={() => handleDeny(user.id)}>
                        Deny
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Active Users */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
               <h2 className="text-xl font-semibold tracking-tight">Active Users</h2>
            </div>
            <Card>
              <CardHeader>
                <CardTitle>Approved Users</CardTitle>
                <CardDescription>Users with active access.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 max-h-[400px] overflow-y-auto">
                {activeUsers.map((user) => (
                  <div key={user.id} className="flex items-center justify-between border-b border-border pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                        {user.identifier[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{user.identifier}</p>
                        <p className="text-xs text-muted-foreground">{user.email || "No email"}</p>
                      </div>
                    </div>
                    <span className="text-xs font-mono bg-primary/10 text-primary px-2 py-1 rounded">
                      {user.role}
                    </span>
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
