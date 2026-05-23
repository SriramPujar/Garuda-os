"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  Compass, 
  Flame, 
  Heart, 
  Activity, 
  BookOpen, 
  ChevronRight, 
  Sparkles, 
  CalendarDays,
  User
} from "lucide-react";
import Link from "next/link";

export default function Home() {
  const [userName, setUserName] = useState("Seeker");
  const [dashboardStats, setDashboardStats] = useState({
    meditationMinutes: 45,
    japaRounds: 8,
    consistencyRatio: 84,
    streak: 3
  });

  useEffect(() => {
    // Check if token and fetch user details
    const token = localStorage.getItem("token");
    if (token) {
      fetch("http://localhost:8000/api/v1/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data.username) setUserName(data.username);
      })
      .catch(() => {});
    }
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="space-y-8"
    >
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-saffron-dim/20 via-card to-background border border-saffron/15 p-8 saffron-glow">
        <h2 className="text-3xl font-bold tracking-tight text-foreground mb-2">
          Hari Om, <span className="text-saffron">{userName}</span>
        </h2>
        <p className="text-sm text-muted-sacred max-w-2xl leading-relaxed">
          Welcome to your Garuda Dharma OS workstation. Your spiritual state is currently assessed as 
          <span className="text-saffron font-semibold"> REFLECTIVE</span>. Let this day be guided by conscious actions 
          and alignment with your Swadharma.
        </p>
      </div>

      {/* Analytics Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { title: "Meditation Time", value: `${dashboardStats.meditationMinutes} mins`, desc: "This week's session logs", icon: Activity, color: "text-blue-400 bg-blue-950/20 border-blue-900/30" },
          { title: "Japa Mantras", value: `${dashboardStats.japaRounds} Rounds`, desc: "1 round = 108 chants", icon: Flame, color: "text-saffron bg-saffron/10 border-saffron/20" },
          { title: "Consistency Index", value: `${dashboardStats.consistencyRatio}%`, desc: "Weekly routine completions", icon: Compass, color: "text-emerald-400 bg-emerald-950/20 border-emerald-900/30" },
          { title: "Daily Streak", value: `${dashboardStats.streak} Days`, desc: "Next threshold: 5 days", icon: Sparkles, color: "text-amber-400 bg-amber-950/20 border-amber-900/30" },
        ].map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className={`rounded-xl border p-5 ${stat.color}`}>
              <div className="flex justify-between items-center mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-sacred">{stat.title}</span>
                <Icon className="h-4.5 w-4.5" />
              </div>
              <p className="text-2xl font-bold text-foreground mb-1">{stat.value}</p>
              <p className="text-[11px] text-muted-sacred leading-tight">{stat.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Bottom Main Content Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recommended Practices */}
        <div className="lg:col-span-2 rounded-xl border border-sacred-border bg-card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground flex items-center gap-2">
              <Heart className="h-4 w-4 text-saffron" />
              <span>Recommended Practices for Today</span>
            </h3>
            <span className="text-[10px] text-saffron bg-saffron/5 px-2 py-0.5 rounded border border-saffron/10 font-medium">Rajasic mind balance</span>
          </div>

          <div className="space-y-3">
            {[
              { name: "Nadi Shodhana Pranayama", time: "10 mins", desc: "Alternate nostril breathing to calm the nervous system and clear mental clutter.", route: "/sadhana" },
              { name: "Contemplation on Gita 2.47", time: "5 mins", desc: "Read and meditate upon the concept of Nishkama Karma (acting without outcome dependency).", route: "/scriptures" },
              { name: "Ganesha Panchopachara Puja", time: "15 mins", desc: "A simple offering of incense and flower to stabilize intention and clear obstacles.", route: "/rituals" }
            ].map((practice, idx) => (
              <div key={idx} className="group flex justify-between items-center rounded-lg bg-background/30 border border-sacred-border p-4 hover:border-saffron/30 hover:bg-card-hover transition-all">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-foreground group-hover:text-saffron transition-colors">{practice.name}</span>
                    <span className="text-[10px] text-muted-sacred bg-background border border-sacred-border px-1.5 py-0.2 rounded">{practice.time}</span>
                  </div>
                  <p className="text-xs text-muted-sacred leading-relaxed max-w-xl">{practice.desc}</p>
                </div>
                <Link href={practice.route}>
                  <button className="flex h-8 w-8 items-center justify-center rounded-full bg-background border border-sacred-border text-muted-sacred group-hover:bg-saffron group-hover:text-background group-hover:border-saffron transition-all">
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* Traditional Calendar / Upcoming Festivals */}
        <div className="rounded-xl border border-sacred-border bg-card p-6 flex flex-col">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground flex items-center gap-2 mb-4">
            <CalendarDays className="h-4 w-4 text-saffron" />
            <span>Spiritual Calendar</span>
          </h3>

          <div className="flex-1 space-y-4">
            {[
              { date: "May 22, 2026", festival: "Shukla Ekadashi Vrat", type: "Fasting & Chanting", highlight: true },
              { date: "May 28, 2026", festival: "Pradosham Puja", type: "Evening Worship", highlight: false },
              { date: "Jun 01, 2026", festival: "Jyeshtha Purnima", type: "Full Moon Meditation", highlight: false }
            ].map((fest, idx) => (
              <div key={idx} className={`flex items-start justify-between border-b border-sacred-border/60 pb-3 last:border-b-0 last:pb-0`}>
                <div className="space-y-0.5">
                  <span className="text-[10px] text-muted-sacred block">{fest.date}</span>
                  <span className={`text-xs font-semibold ${fest.highlight ? "text-saffron" : "text-foreground"}`}>{fest.festival}</span>
                  <span className="text-[10px] text-muted-sacred block">{fest.type}</span>
                </div>
                {fest.highlight && (
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-saffron/10 text-saffron border border-saffron/15 saffron-glow">
                    Auspicious
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-sacred-border text-[11px] text-muted-sacred leading-relaxed">
            <span className="text-foreground font-semibold">Tithi:</span> Panchami, Shukla Paksha | <span className="text-foreground font-semibold">Ritu:</span> Grishma (Summer)
          </div>
        </div>
      </div>
    </motion.div>
  );
}
