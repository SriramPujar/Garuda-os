"use client";

import { useState, useEffect } from "react";
import { Flame, Plus, Check, Award, Compass } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function SadhanaPage() {
  const [routines, setRoutines] = useState<any[]>([]);
  const [streak, setStreak] = useState<any>({ current_streak: 0, max_streak: 0 });
  const [showAddForm, setShowAddForm] = useState(false);
  
  // Form state
  const [name, setName] = useState("");
  const [routineType, setRoutineType] = useState("japa");
  const [targetValue, setTargetValue] = useState(108);
  const [unit, setUnit] = useState("counts");
  const [description, setDescription] = useState("");
  
  // Log states
  const [logValue, setLogValue] = useState<Record<number, number>>({});
  const [logNotes, setLogNotes] = useState<Record<number, string>>({});
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      // Fetch routines
      const rRes = await fetch(`${getApiUrl()}/api/v1/sadhana/routines`, { headers });
      if (rRes.ok) {
        const rData = await rRes.json();
        setRoutines(rData);
      }
      
      // Fetch streak
      const sRes = await fetch(`${getApiUrl()}/api/v1/sadhana/streak`, { headers });
      if (sRes.ok) {
        const sData = await sRes.json();
        setStreak(sData);
      }
    } catch (err) {
      console.error("Failed to load sadhana data: ", err);
    }
  };

  const handleAddRoutine = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please log in or register first under the Settings tab.");
      return;
    }

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/sadhana/routines`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          name,
          routine_type: routineType,
          target_value: Number(targetValue),
          unit,
          description
        })
      });

      if (res.ok) {
        setName("");
        setDescription("");
        setShowAddForm(false);
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogSadhana = async (routineId: number) => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please log in first under the Settings tab.");
      return;
    }

    const value = logValue[routineId] || routines.find(r => r.id === routineId)?.target_value || 108;
    const notes = logNotes[routineId] || "Logged via Sadhana dashboard";

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/sadhana/logs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          routine_id: routineId,
          value_completed: Number(value),
          notes,
          status: "completed"
        })
      });

      if (res.ok) {
        setSuccessMsg("Sadhana logged successfully!");
        setLogNotes(prev => ({ ...prev, [routineId]: "" }));
        fetchData();
        setTimeout(() => setSuccessMsg(""), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Flame className="h-6 w-6 text-saffron saffron-glow" />
          <div>
            <h2 className="text-xl font-semibold text-foreground">Sadhana Disciplines</h2>
            <p className="text-xs text-muted-sacred">Design and maintain structured routines to stabilize your spiritual attention</p>
          </div>
        </div>
        <button 
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 rounded-lg bg-saffron text-background px-4 py-2 text-sm font-semibold hover:bg-saffron-light transition-colors cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>New Routine</span>
        </button>
      </div>

      {/* Streak Dashboard Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-sacred-border bg-card p-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-full bg-saffron/10 text-saffron flex items-center justify-center saffron-glow">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-muted-sacred">Current Active Streak</span>
            <p className="text-xl font-bold text-foreground">{streak.current_streak} Days</p>
          </div>
        </div>
        <div className="rounded-xl border border-sacred-border bg-card p-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-full bg-amber-500/10 text-amber-500 flex items-center justify-center">
            <Award className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-muted-sacred">All-Time Max Streak</span>
            <p className="text-xl font-bold text-foreground">{streak.max_streak} Days</p>
          </div>
        </div>
        <div className="rounded-xl border border-sacred-border bg-card p-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-muted-sacred">Dharmic Standing</span>
            <p className="text-xl font-bold text-foreground">Sattvic Alignment</p>
          </div>
        </div>
      </div>

      {successMsg && (
        <div className="rounded-lg border border-emerald-950/40 bg-emerald-950/10 px-4 py-3 text-xs text-emerald-400 flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Add Routine Form Panel */}
      {showAddForm && (
        <form onSubmit={handleAddRoutine} className="rounded-xl border border-sacred-border bg-card p-6 space-y-4 max-w-xl">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">Add Custom Routine</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Routine Name</label>
              <input 
                type="text" 
                value={name} 
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Morning Japa, Breath Meditation" 
                className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Practice Type</label>
              <select 
                value={routineType} 
                onChange={(e) => setRoutineType(e.target.value)}
                className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:border-saffron"
              >
                <option value="japa">Japa (Chanting)</option>
                <option value="meditation">Dhyana (Meditation)</option>
                <option value="pranayama">Pranayama (Breathing)</option>
                <option value="scripture">Svadhyaya (Scripture study)</option>
                <option value="puja">Puja (Rituals)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Daily Target</label>
              <input 
                type="number" 
                value={targetValue} 
                onChange={(e) => setTargetValue(Number(e.target.value))}
                className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-muted-sacred">Unit</label>
              <input 
                type="text" 
                value={unit} 
                onChange={(e) => setUnit(e.target.value)}
                placeholder="e.g. counts, minutes, chapters" 
                className="w-full rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-muted-sacred">Description</label>
            <textarea 
              value={description} 
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide context or guidance notes..."
              className="w-full h-16 rounded border border-sacred-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none"
            />
          </div>

          <div className="flex gap-2.5 pt-2">
            <button type="submit" className="rounded bg-saffron text-background px-4 py-1.5 text-xs font-semibold hover:bg-saffron-light">
              Save
            </button>
            <button type="button" onClick={() => setShowAddForm(false)} className="rounded border border-sacred-border text-muted-sacred px-4 py-1.5 text-xs hover:bg-card-hover">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Routine Cards Grid List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
        {routines.map((routine) => (
          <div key={routine.id} className="rounded-xl border border-sacred-border bg-card p-5 space-y-4 hover:border-saffron/15 transition-all">
            {/* Header info */}
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-sm text-foreground">{routine.name}</h3>
                <p className="text-[10px] text-muted-sacred leading-relaxed">{routine.description}</p>
              </div>
              <span className="text-[10px] uppercase font-mono px-2.5 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/15 saffron-glow">
                {routine.routine_type}
              </span>
            </div>

            {/* Target information */}
            <div className="text-xs text-muted-sacred">
              <span className="font-semibold text-foreground">Target: </span> 
              {routine.target_value} {routine.unit} daily
            </div>

            {/* Quick Completion Form */}
            <div className="border-t border-sacred-border/60 pt-3.5 space-y-3">
              <span className="text-[10px] uppercase font-bold text-muted-sacred block">Log practice:</span>
              <div className="flex gap-2">
                <input 
                  type="number" 
                  placeholder={String(routine.target_value)}
                  onChange={(e) => setLogValue(prev => ({ ...prev, [routine.id]: Number(e.target.value) }))}
                  className="w-20 rounded border border-sacred-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none"
                />
                <input 
                  type="text" 
                  placeholder="Notes (e.g. felt calm and centered)" 
                  onChange={(e) => setLogNotes(prev => ({ ...prev, [routine.id]: e.target.value }))}
                  className="flex-1 rounded border border-sacred-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none"
                />
                <button 
                  onClick={() => handleLogSadhana(routine.id)}
                  className="rounded bg-saffron/10 border border-saffron/20 text-saffron hover:bg-saffron hover:text-background px-3 py-1 text-xs font-semibold transition-colors cursor-pointer"
                >
                  Log
                </button>
              </div>
            </div>
          </div>
        ))}

        {routines.length === 0 && (
          <p className="text-xs text-muted-sacred italic">No sadhana disciplines registered yet. Add a new routine above.</p>
        )}
      </div>
    </div>
  );
}
