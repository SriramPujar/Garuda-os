"use client";

import { useState, useEffect } from "react";
import { Sparkles, Flower, Gift, Check, Clock } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function RitualsPage() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/rituals/templates`);
      if (res.ok) {
        const data = await res.json();
        setTemplates(data);
        if (data.length > 0) setSelectedTemplate(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogRitual = async () => {
    if (!selectedTemplate) return;
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please log in first under the Settings tab.");
      return;
    }

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/rituals/logs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ritual_name: selectedTemplate.name,
          duration_spent: selectedTemplate.estimated_duration,
          notes: "Completed traditional steps chanting the sacred mantras."
        })
      });

      if (res.ok) {
        setSuccessMsg(`Logged completion of ${selectedTemplate.name}!`);
        setActiveStep(0);
        setTimeout(() => setSuccessMsg(""), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex items-center gap-3">
        <Sparkles className="h-6 w-6 text-saffron saffron-glow" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Rituals & Puja Assistant</h2>
          <p className="text-xs text-muted-sacred">Access step-by-step guidance for traditional Pujas, offerings, and mantra pronunciations</p>
        </div>
      </div>

      {successMsg && (
        <div className="rounded-lg border border-emerald-950/40 bg-emerald-950/10 px-4 py-3 text-xs text-emerald-400">
          {successMsg}
        </div>
      )}

      {/* Main Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Side: Templates List */}
        <div className="space-y-3">
          <span className="text-[10px] uppercase font-bold text-muted-sacred block">Available Rituals</span>
          {templates.map((temp) => (
            <button
              key={temp.id}
              onClick={() => {
                setSelectedTemplate(temp);
                setActiveStep(0);
              }}
              className={`w-full text-left rounded-xl border p-4 transition-all cursor-pointer ${
                selectedTemplate?.id === temp.id
                  ? "border-saffron bg-saffron/5"
                  : "border-sacred-border bg-card hover:border-saffron/40"
              }`}
            >
              <h3 className="font-semibold text-sm text-foreground mb-1">{temp.name}</h3>
              <div className="flex items-center gap-3 text-[10px] text-muted-sacred">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {temp.estimated_duration} mins
                </span>
                <span>Deity: {temp.deity}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Center/Right: Ritual steps player */}
        {selectedTemplate && (
          <div className="lg:col-span-3 rounded-xl border border-sacred-border bg-card p-6 space-y-6">
            
            {/* Template Intro */}
            <div className="border-b border-sacred-border pb-4">
              <h3 className="text-lg font-semibold text-foreground mb-1">{selectedTemplate.name}</h3>
              <p className="text-xs text-muted-sacred">{selectedTemplate.description}</p>
            </div>

            {/* Offerings list */}
            <div>
              <span className="text-[10px] uppercase font-bold text-muted-sacred block mb-2">Required Materials (Upacharas):</span>
              <div className="flex flex-wrap gap-2">
                {JSON.parse(selectedTemplate.offerings_json || "[]").map((item: string, idx: number) => (
                  <span key={idx} className="flex items-center gap-1.5 rounded-lg bg-background border border-sacred-border px-3 py-1 text-xs text-muted-sacred">
                    <Gift className="h-3.5 w-3.5 text-saffron" />
                    {item}
                  </span>
                ))}
              </div>
            </div>

            {/* Step Player */}
            <div className="rounded-xl bg-background/50 border border-sacred-border p-6 space-y-4">
              {/* Steps progression indicator */}
              <div className="flex justify-between items-center border-b border-sacred-border/60 pb-3">
                <span className="text-xs font-semibold text-saffron uppercase tracking-wider">
                  Step {activeStep + 1} of {JSON.parse(selectedTemplate.steps_json).length}
                </span>
                <span className="text-[10px] text-muted-sacred">
                  {JSON.parse(selectedTemplate.steps_json)[activeStep].name}
                </span>
              </div>

              {/* Step text */}
              <p className="text-sm text-foreground leading-relaxed">
                {JSON.parse(selectedTemplate.steps_json)[activeStep].instruction}
              </p>

              {/* Mantra block */}
              {JSON.parse(selectedTemplate.steps_json)[activeStep].mantra && (
                <div className="rounded bg-saffron/5 border border-saffron/10 p-4 text-center space-y-1">
                  <span className="text-[9px] uppercase font-bold tracking-wider text-saffron block">Chant Mantra:</span>
                  <p className="font-serif text-sm text-saffron-light italic">
                    &ldquo;{JSON.parse(selectedTemplate.steps_json)[activeStep].mantra}&rdquo;
                  </p>
                </div>
              )}

              {/* Nav controls */}
              <div className="flex justify-between pt-2">
                <button
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep(prev => prev - 1)}
                  className="rounded border border-sacred-border px-4 py-1.5 text-xs text-muted-sacred hover:bg-card-hover disabled:opacity-30 cursor-pointer"
                >
                  Previous
                </button>
                {activeStep < JSON.parse(selectedTemplate.steps_json).length - 1 ? (
                  <button
                    onClick={() => setActiveStep(prev => prev + 1)}
                    className="rounded bg-saffron text-background px-4 py-1.5 text-xs font-semibold hover:bg-saffron-light cursor-pointer"
                  >
                    Next Step
                  </button>
                ) : (
                  <button
                    onClick={handleLogRitual}
                    className="rounded bg-emerald-600 text-foreground px-5 py-1.5 text-xs font-semibold hover:bg-emerald-500 flex items-center gap-1.5 cursor-pointer saffron-glow"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>Complete Puja</span>
                  </button>
                )}
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
