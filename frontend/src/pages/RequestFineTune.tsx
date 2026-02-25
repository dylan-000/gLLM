import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Send, CheckCircle2, ArrowLeft, Terminal, MessageSquare } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

export default function RequestFinetune() {
  const navigate = useNavigate();
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Will implement endpoint later
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1500);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6 font-sans">
        <Card className="max-w-md w-full border-border shadow-lg animate-in fade-in zoom-in duration-300">
          <CardContent className="pt-10 pb-10 text-center space-y-6">
            <div className="mx-auto w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
              <CheckCircle2 className="h-10 w-10 text-primary" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">Request Submitted</h2>
              <p className="text-muted-foreground">
                Your proposal has been sent to the administration team. You will be notified via email once your request is reviewed.
              </p>
            </div>
            <Button onClick={() => navigate("/")} className="w-full">
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
      <header className="h-16 border-b border-border flex items-center px-6 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <Button variant="ghost" size="sm" onClick={() => navigate("/")} className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
      </header>

      <main className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="max-w-2xl w-full space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Terminal className="h-8 w-8 text-secondary" />
              Fine-Tuning Access Request
            </h1>
            <p className="text-muted-foreground text-lg">
              Submit a proposal to gain access to Unsloth Studio and fine-tune models on your domain.
            </p>
          </div>

          <Card className="border-border shadow-md">
            <CardHeader className="border-b border-border/50 bg-muted/20">
              <CardTitle>Proposal Details</CardTitle>
              <CardDescription>Explain your objectives.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="domain">Target Domain / Topic</Label>
                  <Input 
                    id="domain" 
                    placeholder="e.g. MATLAB, Python, Perovskite Solar Cells" 
                    required 
                    className="bg-background"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">What would you like to fine-tune the model on?</Label>
                  <textarea 
                    id="description"
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="Describe your dataset and the specific behaviors you want the model to learn..."
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="necessity">Why is fine-tuning necessary for your cause?</Label>
                  <textarea 
                    id="necessity"
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    placeholder="Explain why standard RAG or base models are insufficient for your requirements..."
                    required
                  />
                </div>

                <div className="pt-4 flex flex-col md:flex-row gap-4">
                  <Button type="submit" className="flex-1 gap-2 py-6 text-base" disabled={loading}>
                    {loading ? "Sending..." : (
                      <>
                        <Send className="h-4 w-4" /> Submit Request
                      </>
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => navigate("/")} className="py-6 text-base">
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary/5 border border-secondary/20">
             <div className="p-2 rounded-full bg-secondary/10">
                <MessageSquare className="h-5 w-5 text-secondary" />
             </div>
             <p className="text-xs text-muted-foreground">
                <span className="font-semibold text-foreground">Note:</span> Fine-tuning access is high-resource and granted based on the technical validity and necessity of the proposed use case.
             </p>
          </div>
        </div>
      </main>
    </div>
  );
}