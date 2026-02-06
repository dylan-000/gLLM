import { useNavigate } from "react-router-dom";
import { ArrowLeft, Users, Database, Activity, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Input } from "../components/ui/input";

export default function AdminPanel() {
  const navigate = useNavigate();

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
          <div className="flex items-center gap-4">
             <div className="relative hidden md:block">
               <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
               <Input placeholder="Search logs..." className="pl-9 w-64 h-9" />
             </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6 md:p-8 space-y-8">
        
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <AdminStatCard 
            title="Total Users" 
            value="142" 
            desc="+12 this week" 
            icon={<Users className="h-5 w-5 text-blue-500" />} 
          />
          <AdminStatCard 
            title="Active Containers" 
            value="8/10" 
            desc="Operating normally" 
            icon={<Database className="h-5 w-5 text-green-500" />} 
          />
          <AdminStatCard 
            title="Error Rate" 
            value="0.4%" 
            desc="Last 24 hours" 
            icon={<Activity className="h-5 w-5 text-orange-500" />} 
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

          {/* System Logs Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
               <h2 className="text-xl font-semibold tracking-tight">System Logs</h2>
               <Button variant="outline" size="sm">Export</Button>
            </div>
            <Card className="bg-black/95 text-green-400 font-mono text-xs p-4 h-[300px] overflow-y-auto border-border shadow-inner">
               <p>[10:42:01] INFO: vLLM server started on port 8000</p>
               <p>[10:42:05] INFO: Model 'Qwen2.5-Coder' loaded successfully</p>
               <p>[10:45:12] WARN: High memory usage detected (85%)</p>
               <p>[10:46:00] INFO: User 'nenglert' initiated session</p>
               <p>[10:48:22] ERROR: Connection timeout for Container ID #4421</p>
               <p className="animate-pulse">_</p>
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