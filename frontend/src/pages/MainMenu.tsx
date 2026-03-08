import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { MessageSquare, Settings, Shield, Terminal, LogOut, Menu, LayoutDashboard, Moon, Sun } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { UserRole } from "../models/User";
import { useTheme } from "../contexts/ThemeContext";
import { useAuth } from "../contexts/AuthContext";
import { getToken } from "../services/api";

export default function MainMenu() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  if (!user) return null;

  const handleNavigation = (path: string) => {
    if (path === "/chat") {
      // Send JWT as bearer header for Chainlit authentication
      const token = getToken();
      if (token) {
        window.location.href = `/gllm/?bearer=${encodeURIComponent(token)}`;
      } else {
        window.location.href = "/gllm/";
      }
    } else if (path.startsWith("http")) {
      window.open(path, "_blank");
    } else {
      navigate(path);
    }
  };

  const handleSignOut = () => {
    logout();
    navigate("/login");
  };

  const displayName = [user.firstname, user.lastname].filter(Boolean).join(" ") || user.identifier;
  const initials = user.firstname && user.lastname
    ? `${user.firstname[0]}${user.lastname[0]}`
    : user.identifier[0].toUpperCase();

  return (
    <div className="min-h-screen bg-background text-foreground flex transition-colors duration-300 font-sans">

      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? 'w-64' : 'w-20'}
        bg-card border-r border-border transition-all duration-300 flex flex-col fixed h-full z-20 shadow-sm`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center px-4 border-b border-border justify-between">
          {sidebarOpen ? (
            <div className="flex items-center gap-2 font-bold text-xl text-primary tracking-tight">
               <img src="/gLLM_ICON.png" alt="Logo" className="h-8 w-8 object-contain" />
               gLLM
            </div>
          ) : (
            <img src="/gLLM_ICON.png" alt="Logo" className="h-8 w-8 mx-auto" />
          )}
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} className="hidden md:flex">
            <Menu className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 p-3 space-y-1 mt-2">
          <SidebarLink icon={<LayoutDashboard />} label="Dashboard" active />
          <SidebarLink icon={<MessageSquare />} label="Chat Agent" onClick={() => handleNavigation("/chat")} />

          {user.role === UserRole.ADMIN && (
             <SidebarLink icon={<Shield />} label="Admin Console" onClick={() => handleNavigation("/admin")} />
          )}

          {(user.role === UserRole.ADMIN || user.role === UserRole.FINE_TUNER) && (
             <SidebarLink icon={<Terminal />} label="Fine-Tuning" onClick={() => handleNavigation("https://unsloth.ai")} />
          )}
        </nav>

        {/* User Footer */}
        <div className="p-4 border-t border-border">
          <Button
            variant="ghost"
            className={`w-full justify-start ${!sidebarOpen && 'px-2 justify-center'}`}
            onClick={toggleTheme}
          >
            {theme === 'dark' ? (
                <Sun className="h-4 w-4" />
            ) : (
                <Moon className="h-4 w-4" />
            )}
            {sidebarOpen && <span className="ml-2">
                {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </span>}
          </Button>
          <Button
            variant="ghost"
            className={`w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10 ${!sidebarOpen && 'px-2 justify-center'}`}
            onClick={handleSignOut}
          >
            <LogOut className="h-4 w-4" />
            {sidebarOpen && <span className="ml-2">Sign Out</span>}
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 p-6 md:p-8 transition-all duration-300 ${sidebarOpen ? 'md:ml-64' : 'md:ml-20'} ml-0`}>

        {/* Page Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">gLLM Dashboard</h1>
          </div>
          <div className="flex items-center gap-3">
             <span className="text-xs font-mono bg-primary/10 text-primary border border-primary/20 px-3 py-1 rounded-full uppercase">
               System: Online
             </span>
             <span className="text-xs font-mono bg-secondary/10 text-secondary border border-secondary/20 px-3 py-1 rounded-full uppercase">
               vLLM: Active
             </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Main Applications */}
            <h2 className="text-lg font-semibold tracking-tight">Applications</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
               <ActionCard
                 title="Launch gLLM Agent"
                 desc="Start a new chat session with the domain adaptable model."
                 icon={<MessageSquare className="h-6 w-6 text-primary" />}
                 onClick={() => handleNavigation("/chat")}
               />

               {user.role === UserRole.ADMIN && (
                 <ActionCard
                   title="System Administration"
                   desc="Manage docker containers, user roles, and logs."
                   icon={<Shield className="h-6 w-6 text-chart-1" />}
                   onClick={() => handleNavigation("/admin")}
                 />
               )}

               {(user.role === UserRole.FINE_TUNER || user.role === UserRole.ADMIN) && (
                 <ActionCard
                   title="Fine-Tune Models"
                   desc="Access Jupyter interface for model training."
                   icon={<Terminal className="h-6 w-6 text-secondary" />}
                   onClick={() => handleNavigation("https://unsloth.ai")}
                 />
               )}

               {user.role === UserRole.NORMAL && (
                 <ActionCard
                   title="Request Access"
                   desc="Submit request for fine-tuning privileges."
                   icon={<Settings className="h-6 w-6 text-muted-foreground" />}
                   onClick={() => handleNavigation("/request-access")}
                 />
               )}
            </div>
          </div>

          {/* Profile */}
          <div className="space-y-6">
            <h2 className="text-lg font-semibold tracking-tight">Your Profile</h2>
            <Card className="border-border shadow-sm">
              <CardHeader className="pb-3 border-b border-border/50">
                 <div className="flex items-center gap-3">
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xl">
                      {initials}
                    </div>
                    <div>
                      <CardTitle className="text-lg">{displayName}</CardTitle>
                      <CardDescription>{user.role}</CardDescription>
                    </div>
                 </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                 <ProfileField label="Username" value={user.identifier} />
                 <ProfileField label="Email" value={user.email || "—"} />
                 <ProfileField label="Access Level" value={user.role.toUpperCase()} />

                 <Button variant="outline" className="w-full mt-2">
                   <Settings className="mr-2 h-4 w-4" /> Edit Profile
                 </Button>
              </CardContent>
            </Card>

            <Card className="bg-muted/30 border-dashed">
               <CardContent className="p-6 text-center text-muted-foreground text-sm">
                  No recent system notifications.
               </CardContent>
            </Card>
          </div>

        </div>
      </main>
    </div>
  );
}

function SidebarLink({ icon, label, onClick, active }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center w-full p-2.5 rounded-lg transition-colors duration-200 group
        ${active ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}
      `}
    >
      <span className={active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground'}>{icon}</span>
      <span className="ml-3 text-sm truncate">{label}</span>
    </button>
  );
}

function ActionCard({ title, desc, icon, onClick }: any) {
  return (
    <div
      onClick={onClick}
      className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-primary/50 cursor-pointer"
    >
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <h3 className="font-semibold text-lg leading-none tracking-tight group-hover:text-primary transition-colors">{title}</h3>
          <p className="text-sm text-muted-foreground">{desc}</p>
        </div>
        <div className="p-2 rounded-lg bg-accent group-hover:bg-primary/10 transition-colors">
          {icon}
        </div>
      </div>
    </div>
  )
}

function ProfileField({ label, value }: any) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  )
}
