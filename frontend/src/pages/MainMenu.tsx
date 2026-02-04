import { useNavigate } from "react-router-dom";
import { MessageSquare, Settings, Shield, Terminal, LogOut } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { UserRole } from "../models/User";

// Temporary Role
const CURRENT_USER_ROLE: UserRole = UserRole.ADMIN; 

export default function MainMenu() {
  const navigate = useNavigate();
  const role: UserRole = CURRENT_USER_ROLE;

  const handleNavigation = (path: string, external = false) => {
    if (external) window.open(path, "_blank");
    else if (path.startsWith("/chat")) window.location.href = path;
    else navigate(path);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex justify-between items-center border-b pb-6">
          <div className="flex items-center gap-4">
            <img src="/gLLM_ICON.png" alt="Logo" className="h-12 w-12 object-contain" />
            <div>
              <h1 className="text-2xl font-bold text-primary">gLLM Dashboard</h1>
              <div className="flex items-center gap-2">
                 <span className="text-sm text-muted-foreground">Role:</span>
                 <span className="text-xs font-mono bg-secondary/20 text-secondary-foreground px-2 py-0.5 rounded uppercase">
                   {role}
                 </span>
              </div>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={() => navigate("/login")}>
            <LogOut className="mr-2 h-4 w-4" /> Sign Out
          </Button>
        </header>

        {/* --- MAIN MENU GRID --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

          {/* Chainlit */}
          <MenuCard
            title="Launch gLLM Agent"
            description="Chat with the Domain Adaptable model."
            icon={<MessageSquare className="h-8 w-8 text-primary" />}
            onClick={() => handleNavigation("/chat")}
          />

          {/* ADMIN */}
          {role === UserRole.ADMIN && (
            <MenuCard
              title="Admin Console"
              description="Manage system configurations, users, and containers."
              icon={<Shield className="h-8 w-8 text-chart-1" />}
              onClick={() => handleNavigation("/admin")} 
            />
          )}

          {/* FINETUNER */}
          {role === UserRole.FINETUNER && (
            <MenuCard
              title="Fine-Tune Models"
              description="Access the Unsloth interface to train new models."
              icon={<Terminal className="h-8 w-8 text-secondary" />}
              onClick={() => handleNavigation("https://unsloth.ai", true)} 
            />
          )}

          {/* REGULAR USER */}
          {role === UserRole.REGUSER && (
            <MenuCard
              title="Request Upgrade"
              description="Submit a request to gain fine-tuning privileges."
              icon={<Settings className="h-8 w-8 text-muted-foreground" />}
              onClick={() => console.log("Request Submitted")}
            />
          )}

        </div>
      </div>
    </div>
  );
}

function MenuCard({ title, description, icon, onClick }: any) {
  return (
    <Card onClick={onClick} className="cursor-pointer hover:border-primary/50 hover:shadow-lg transition-all group">
      <CardHeader className="flex flex-row items-center gap-4 pb-2">
        <div className="p-3 rounded-lg bg-accent group-hover:bg-accent/80 transition-colors">
          {icon}
        </div>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  );
}