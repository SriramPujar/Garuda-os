"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Bell, Mic, Cpu } from "lucide-react";

const PAGE_TITLES: Record<string, string> = {
  "/": "Home",
  "/chat": "Dharma Chat",
  "/scriptures": "Sacred Scriptures",
  "/sadhana": "Sadhana Tracker",
  "/journal": "Journal & Reflection",
  "/rituals": "Rituals & Puja",
  "/festivals": "Festivals",
  "/spiritualtube": "Garuda SpiritualTube",
  "/nada": "Garuda Nada",
  "/workspace": "Consciousness Workspace",
  "/settings": "Settings",
};

export default function TopBar() {
  const pathname = usePathname();
  const [spiritualState, setSpiritualState] = useState({
    state: "reflective",
    color: "border-saffron/40 text-saffron bg-saffron/5",
  });

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetch("http://localhost:8000/api/v1/sadhana/streak", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then(() => {
          setSpiritualState({
            state: "disciplined",
            color: "border-emerald-500/40 text-emerald-400 bg-emerald-950/20",
          });
        })
        .catch(() => {});
    }
  }, []);

  const title = PAGE_TITLES[pathname] ?? "Garuda Dharma OS";

  return (
    <header className="flex h-12 w-full shrink-0 items-center justify-between border-b border-sacred-border/50 bg-background/80 backdrop-blur-sm px-5">
      {/* Page Title */}
      <div className="flex items-center gap-2.5">
        <span className="text-saffron text-base select-none">✦</span>
        <h2 className="text-sm font-semibold tracking-wide text-foreground">{title}</h2>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-3">
        {/* Orchestrator Status */}
        <div className="hidden md:flex items-center gap-2 border-r border-sacred-border/50 pr-3 text-xs text-muted-sacred">
          <Cpu className="h-3.5 w-3.5 text-saffron" />
          <div className="flex gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500" style={{ boxShadow: "0 0 4px #22c55e" }} title="Dharma Guide Ready" />
            <span className="h-2 w-2 rounded-full bg-emerald-500" title="Scholar Ready" />
            <span className="h-2 w-2 rounded-full bg-amber-500" title="Sadhana Coach Idle" />
          </div>
        </div>

        {/* Spiritual State */}
        <div className={`hidden md:flex px-2.5 py-0.5 rounded-full text-[10px] font-bold border tracking-widest uppercase ${spiritualState.color}`}>
          {spiritualState.state}
        </div>

        {/* Mic */}
        <button
          suppressHydrationWarning
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-sacred-border/50 hover:bg-card hover:border-saffron/40 transition-colors"
          title="Voice Mode"
        >
          <Mic className="h-3.5 w-3.5 text-muted-sacred" />
        </button>

        {/* Bell */}
        <button 
          suppressHydrationWarning
          className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-sacred-border/50 hover:bg-card transition-colors"
        >
          <Bell className="h-3.5 w-3.5 text-muted-sacred" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-saffron" />
        </button>
      </div>
    </header>
  );
}
