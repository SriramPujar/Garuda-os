"use client";

import { useState, useEffect } from "react";
import { BookOpen, Compass, Heart, AlertCircle, Smile } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function JournalPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [content, setContent] = useState("");
  const [promptUsed, setPromptUsed] = useState("Explain how you felt today. Did you act with attachment to outcomes?");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  const journalPrompts = [
    "Did you practice Nishkama Karma today? Explain where you succeeded or failed.",
    "What mental obstacles (Rajas/Tamas) pulled you away from stillness today?",
    "Reflect on a situation where you chose the good (Shreyas) over the pleasant (Preyas).",
    "Where did you notice the presence of Grace or peace today?"
  ];

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/journal`, { headers });
      if (res.ok) {
        const data = await res.json();
        setEntries(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmitJournal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || loading) return;

    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please register or log in first under the Settings tab.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/journal`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          content,
          prompt_used: promptUsed
        })
      });

      if (res.ok) {
        setContent("");
        setSuccessMsg("Journal entry logged and analyzed by the Reflection Agent!");
        fetchEntries();
        setTimeout(() => setSuccessMsg(""), 3000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex items-center gap-3">
        <BookOpen className="h-6 w-6 text-saffron saffron-glow" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Reflection & Introspection Journal</h2>
          <p className="text-xs text-muted-sacred">Document your spiritual struggles and insights. Logs are analyzed locally to map emotional trends</p>
        </div>
      </div>

      {successMsg && (
        <div className="rounded-lg border border-emerald-950/40 bg-emerald-950/10 px-4 py-3 text-xs text-emerald-400">
          {successMsg}
        </div>
      )}

      {/* Main Grid: Input and History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side: Write Entry */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Prompts list selector */}
          <div className="rounded-xl border border-sacred-border bg-card p-4">
            <span className="text-[10px] uppercase font-bold text-muted-sacred block mb-2">Select Contemplation Prompt:</span>
            <div className="flex flex-wrap gap-2">
              {journalPrompts.map((p, idx) => (
                <button 
                  key={idx}
                  onClick={() => setPromptUsed(p)}
                  className={`text-left text-xs px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
                    promptUsed === p 
                      ? "border-saffron text-saffron bg-saffron/5" 
                      : "border-sacred-border text-muted-sacred hover:border-saffron/40 hover:text-foreground"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmitJournal} className="space-y-3">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-muted-sacred block">Selected Prompt:</span>
              <p className="text-xs text-saffron-light italic">{promptUsed}</p>
            </div>
            
            <textarea 
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your reflections here..." 
              className="w-full h-64 rounded-xl border border-sacred-border bg-card p-4 text-sm text-foreground focus:outline-none focus:border-saffron/40"
              required
            />
            
            <button 
              type="submit" 
              disabled={loading || !content.trim()}
              className="rounded-lg bg-saffron text-background px-6 py-2.5 text-sm font-semibold hover:bg-saffron-light transition-colors disabled:opacity-50 cursor-pointer"
            >
              {loading ? "Analyzing Entry..." : "Submit to Journal"}
            </button>
          </form>
        </div>

        {/* Right Side: History logs */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">Reflection Logs</h3>
          
          <div className="space-y-3 max-h-[calc(100vh-14rem)] overflow-y-auto pr-2">
            {entries.map((entry, idx) => (
              <div key={idx} className="rounded-xl border border-sacred-border bg-card p-4 space-y-2.5">
                <span className="text-[10px] text-muted-sacred block border-b border-sacred-border/60 pb-1.5">
                  {new Date(entry.created_at).toLocaleDateString()} at {new Date(entry.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                
                <p className="text-xs text-foreground italic leading-relaxed line-clamp-3">
                  &ldquo;{entry.content}&rdquo;
                </p>

                {/* Analysis tags */}
                <div className="flex flex-wrap gap-1.5 pt-1.5">
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/10">
                    Emotion: {entry.dominant_emotion}
                  </span>
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-background border border-sacred-border text-muted-sacred">
                    Depth: {entry.reflection_depth}/5
                  </span>
                </div>
              </div>
            ))}

            {entries.length === 0 && (
              <p className="text-xs text-muted-sacred italic">No previous reflections. Write your first entry to begin.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
