"use client";

import { useState, useEffect } from "react";
import { Flame, Sparkles, BookMarked, Eye } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function ContextPanel() {
  const [streakData, setStreakData] = useState({ current_streak: 3, max_streak: 12 });
  const [routines, setRoutines] = useState<any[]>([]);
  const [dailyVerse, setDailyVerse] = useState<any>({
    scripture: "Bhagavad Gita",
    verse: "2.47",
    sanskrit: "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।",
    translation: "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action."
  });

  useEffect(() => {
    // Fetch values from local backend if available
    const token = localStorage.getItem("token");
    if (token) {
      // Fetch streak
      fetch(`${getApiUrl()}/api/v1/sadhana/streak`, {
        headers: { "Authorization": `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setStreakData(data))
      .catch(() => {});

      // Fetch active routines
      fetch(`${getApiUrl()}/api/v1/sadhana/routines`, {
        headers: { "Authorization": `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setRoutines(data.slice(0, 3)))
      .catch(() => {});

      // Fetch daily verse
      fetch(`${getApiUrl()}/api/v1/scriptures/daily-verse`)
      .then(res => res.json())
      .then(data => setDailyVerse(data))
      .catch(() => {});
    } else {
      // Seed some default items for viewing pleasure
      setRoutines([
        { id: 1, name: "Pranayama Breathing", target_value: 10, unit: "minutes", routine_type: "pranayama" },
        { id: 2, name: "Gita Study", target_value: 1, unit: "chapters", routine_type: "scripture" }
      ]);
    }
  }, []);

  return (
    <aside className="w-80 border-l border-sacred-border bg-card p-6 overflow-y-auto text-foreground">
      {/* Daily Quote Segment */}
      <div className="mb-6 rounded-lg bg-background/40 border border-saffron/10 p-4">
        <div className="flex items-center gap-2 mb-2 text-saffron text-xs font-semibold uppercase tracking-wider">
          <BookMarked className="h-3.5 w-3.5" />
          <span>Daily Contemplation</span>
        </div>
        <p className="text-center font-serif text-[13px] text-saffron-light italic mb-2">
          {dailyVerse.sanskrit}
        </p>
        <p className="text-xs text-muted-sacred leading-relaxed mb-1">
          &ldquo;{dailyVerse.translation}&rdquo;
        </p>
        <span className="text-[10px] text-saffron font-medium">
          — {dailyVerse.scripture} {dailyVerse.verse}
        </span>
      </div>

      {/* Streak Dashboard Card */}
      <div className="mb-6 rounded-lg bg-background/30 border border-sacred-border p-4 flex items-center justify-between">
        <div>
          <h3 className="text-xs text-muted-sacred uppercase tracking-wider font-semibold">Sadhana Streak</h3>
          <span className="text-2xl font-bold text-foreground">{streakData.current_streak} Days</span>
          <p className="text-[10px] text-muted-sacred">Record: {streakData.max_streak} days</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-saffron/10 text-saffron saffron-glow">
          <Flame className="h-6 w-6" />
        </div>
      </div>

      {/* Active Routines checklist */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3 text-xs uppercase tracking-wider text-muted-sacred font-semibold">
          <Sparkles className="h-3.5 w-3.5 text-saffron" />
          <span>Active Sadhana routines</span>
        </div>
        {routines.length === 0 ? (
          <p className="text-xs text-muted-sacred italic">No active routines. Go to Sadhana view to add one.</p>
        ) : (
          <div className="space-y-2">
            {routines.map((routine) => (
              <div key={routine.id} className="flex items-center justify-between rounded bg-background/20 p-2.5 border border-sacred-border text-xs">
                <div>
                  <p className="font-medium text-foreground">{routine.name}</p>
                  <p className="text-[10px] text-muted-sacred">Target: {routine.target_value} {routine.unit}</p>
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/10">
                  {routine.routine_type}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Memory Insights / Guidance */}
      <div>
        <div className="flex items-center gap-2 mb-3 text-xs uppercase tracking-wider text-muted-sacred font-semibold">
          <Eye className="h-3.5 w-3.5 text-saffron" />
          <span>Cognitive Insights</span>
        </div>
        <div className="rounded-lg bg-saffron/5 border border-saffron/10 p-3.5 text-xs text-muted-sacred leading-relaxed">
          <span className="text-saffron font-medium block mb-1">Observation on Gunas:</span>
          Anxiety flags in last journal suggests Rajasic state. Focus on breathwork and Gita 2.47 for stabilization.
        </div>
      </div>
    </aside>
  );
}
