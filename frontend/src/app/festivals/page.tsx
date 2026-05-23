"use client";

import { useState } from "react";
import { Calendar, Bell, Info, Sun, Moon } from "lucide-react";

export default function FestivalsPage() {
  const [reminders, setReminders] = useState<Record<string, boolean>>({
    "Ekadashi": true,
    "Pradosham": false,
    "Purnima": true
  });

  const upcomingFestivals = [
    { name: "Shukla Ekadashi Vrat", date: "May 22, 2026", description: "Fasting from grains. Auspicious for chanting Vishnu Sahasranama.", timing: "Parana: May 23, 05:45 AM - 09:30 AM", type: "Vrata" },
    { name: "Pradosham Puja", date: "May 28, 2026", description: "Twilight worship of Lord Shiva. Ideal time for chanting Sri Rudram.", timing: "Sandhya Timing: 06:12 PM - 08:35 PM", type: "Worship" },
    { name: "Jyeshtha Purnima", date: "June 01, 2026", description: "Full moon. Auspicious for meditation, charity, and Satyanarayan Puja.", timing: "Full Moon starts: May 31, 09:12 PM", type: "Meditation" },
    { name: "Nirjala Ekadashi", date: "June 10, 2026", description: "Waterless fast. One of the most powerful spiritual fasts of the year.", timing: "Total fast, no water allowed.", type: "Vrata" }
  ];

  const toggleReminder = (name: string) => {
    setReminders(prev => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex items-center gap-3">
        <Calendar className="h-6 w-6 text-saffron saffron-glow" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Auspicious Calendar & Timings</h2>
          <p className="text-xs text-muted-sacred">Track Panchang details, upcoming Vrata fasts, and festival reminders</p>
        </div>
      </div>

      {/* Panchang Info card */}
      <div className="rounded-xl border border-sacred-border bg-card p-6 grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-muted-sacred">Tithi (Lunar Day)</span>
          <p className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Moon className="h-4 w-4 text-saffron" />
            Panchami, Shukla Paksha
          </p>
          <span className="text-[10px] text-muted-sacred leading-none">Waxing phase, 5th day</span>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-muted-sacred">Nakshatra (Constellation)</span>
          <p className="text-sm font-semibold text-foreground flex items-center gap-1.5">
            <Sun className="h-4 w-4 text-saffron" />
            Punarvasu
          </p>
          <span className="text-[10px] text-muted-sacred leading-none">Governed by Aditi</span>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-muted-sacred">Yoga & Karana</span>
          <p className="text-sm font-semibold text-foreground">Dhriti & Bava</p>
          <span className="text-[10px] text-muted-sacred leading-none">Auspicious for undertakings</span>
        </div>
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-muted-sacred">Rahukaal (Inauspicious)</span>
          <p className="text-sm font-semibold text-red-400">01:30 PM - 03:00 PM</p>
          <span className="text-[10px] text-muted-sacred leading-none">Avoid initiating new actions</span>
        </div>
      </div>

      {/* Festivals List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Festival List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">Upcoming Celebrations</h3>
          
          <div className="space-y-3">
            {upcomingFestivals.map((fest, idx) => (
              <div key={idx} className="rounded-xl border border-sacred-border bg-card p-5 space-y-3 hover:border-saffron/15 transition-all">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] text-saffron font-semibold uppercase tracking-wider block mb-0.5">{fest.date}</span>
                    <h4 className="font-semibold text-sm text-foreground">{fest.name}</h4>
                  </div>
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-background border border-sacred-border text-muted-sacred">
                    {fest.type}
                  </span>
                </div>
                
                <p className="text-xs text-muted-sacred leading-relaxed">{fest.description}</p>
                
                <div className="flex items-center gap-2 rounded bg-background/40 border border-sacred-border/60 p-2.5 text-[11px] text-muted-sacred">
                  <Info className="h-3.5 w-3.5 text-saffron shrink-0" />
                  <span>{fest.timing}</span>
                </div>

                <div className="flex justify-end pt-1">
                  <button 
                    onClick={() => toggleReminder(fest.name)}
                    className={`flex items-center gap-1.5 text-[10px] uppercase px-3 py-1 rounded border transition-all cursor-pointer ${
                      reminders[fest.name]
                        ? "border-saffron text-saffron bg-saffron/5"
                        : "border-sacred-border text-muted-sacred hover:border-saffron/30 hover:text-foreground"
                    }`}
                  >
                    <Bell className="h-3 w-3" />
                    <span>{reminders[fest.name] ? "Reminder Active" : "Set Reminder"}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Vrata / Fasting Guideline Insights */}
        <div className="rounded-xl border border-sacred-border bg-card p-6 space-y-4 h-fit">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground">Vrata Fasting Guidance</h3>
          
          <div className="space-y-3 text-xs text-muted-sacred leading-relaxed">
            <p>
              Fasting (Vrata) is not merely a restriction of food, but a purification of the body and mind (tapas) to channel energy inward for contemplation.
            </p>
            <div className="border-t border-sacred-border/60 pt-3">
              <span className="text-foreground font-semibold block mb-1">Standard Ekadashi Rules:</span>
              <ul className="list-disc pl-4 space-y-1">
                <li>Avoid all grains, rice, wheat, and beans.</li>
                <li>Consume light foods like milk, fruits, nuts, and sago (sabudana).</li>
                <li>Dedicate the day to extra rounds of Japa and reading scriptures.</li>
                <li>Avoid speaking harsh words or getting angry.</li>
              </ul>
            </div>
            <div className="border-t border-sacred-border/60 pt-3">
              <span className="text-foreground font-semibold block mb-1">Why Fasting?</span>
              According to Ayurveda and Yoga, fasting digests accumulated mental and physical toxins (Ama), shifting the energy from the digestive tract back to the nervous system and intellect (Buddhi).
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
