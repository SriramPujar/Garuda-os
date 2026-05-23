"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import {
  Home,
  MessageCircle,
  BookOpen,
  Flame,
  BookOpenCheck,
  Sparkles,
  Calendar,
  Tv,
  Music,
  Network,
  Settings,
  ShieldAlert,
} from "lucide-react";

const navGroups = [
  {
    label: "Core",
    items: [
      { name: "Home", href: "/", icon: Home },
      { name: "Dharma Chat", href: "/chat", icon: MessageCircle },
      { name: "Scriptures", href: "/scriptures", icon: BookOpen },
      { name: "Sadhana", href: "/sadhana", icon: Flame },
      { name: "Journal", href: "/journal", icon: BookOpenCheck },
    ],
  },
  {
    label: "Practice",
    items: [
      { name: "Rituals & Puja", href: "/rituals", icon: Sparkles },
      { name: "Festivals", href: "/festivals", icon: Calendar },
      { name: "SpiritualTube", href: "/spiritualtube", icon: Tv },
      { name: "Garuda Nada", href: "/nada", icon: Music },
      { name: "Workspace", href: "/workspace", icon: Network },
    ],
  },
  {
    label: "System",
    items: [
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      onHoverStart={() => setExpanded(true)}
      onHoverEnd={() => setExpanded(false)}
      animate={{ width: expanded ? 240 : 56 }}
      transition={{ type: "spring", stiffness: 320, damping: 32 }}
      className="fixed left-0 top-0 z-50 flex h-screen flex-col overflow-hidden border-r border-sacred-border/50 bg-card/95 backdrop-blur-xl"
      style={{ boxShadow: expanded ? "4px 0 32px rgba(0,0,0,0.35)" : "none" }}
    >
      {/* Brand Header */}
      <div className="flex h-12 shrink-0 items-center gap-3 border-b border-sacred-border/40 px-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-saffron text-background font-bold text-base shadow-md" style={{ boxShadow: "0 0 12px rgba(251,146,60,0.4)" }}>
          ॐ
        </div>
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.18 }}
              className="overflow-hidden whitespace-nowrap"
            >
              <p className="text-sm font-semibold tracking-wide leading-tight">Garuda Dharma</p>
              <p className="text-[10px] text-saffron font-medium">OS v2.0</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Groups */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-1">
        {navGroups.map((group) => (
          <div key={group.label}>
            {/* Group label — only when expanded */}
            <AnimatePresence>
              {expanded && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="px-3 pt-3 pb-1 text-[9px] uppercase tracking-widest font-bold text-muted-sacred/50 whitespace-nowrap"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>

            {group.items.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <div key={item.href} className="relative group/item">
                  <Link href={item.href} className="block">
                    <div
                      className={`relative flex items-center gap-3 mx-1.5 my-0.5 rounded-lg px-2.5 py-2 transition-all duration-150 cursor-pointer ${
                        isActive
                          ? "bg-saffron/10 text-saffron"
                          : "text-muted-sacred hover:bg-white/5 hover:text-foreground"
                      }`}
                    >
                      {/* Active pill */}
                      {isActive && (
                        <motion.div
                          layoutId="activeNavPill"
                          className="absolute inset-0 rounded-lg bg-saffron/10 border border-saffron/25"
                          transition={{ type: "spring", stiffness: 400, damping: 35 }}
                        />
                      )}

                      <Icon
                        className={`relative z-10 h-4 w-4 shrink-0 ${isActive ? "text-saffron" : ""}`}
                        style={isActive ? { filter: "drop-shadow(0 0 6px rgba(251,146,60,0.6))" } : {}}
                      />

                      <AnimatePresence>
                        {expanded && (
                          <motion.span
                            initial={{ opacity: 0, x: -6 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -6 }}
                            transition={{ duration: 0.16 }}
                            className="relative z-10 text-xs font-medium whitespace-nowrap overflow-hidden"
                          >
                            {item.name}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </div>
                  </Link>

                  {/* Tooltip when collapsed */}
                  {!expanded && (
                    <div className="pointer-events-none absolute left-14 top-1/2 -translate-y-1/2 z-[100] hidden group-hover/item:block">
                      <div className="rounded-md bg-card border border-sacred-border px-2.5 py-1.5 text-xs font-medium text-foreground shadow-lg whitespace-nowrap">
                        {item.name}
                        <div className="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-1.5 h-1.5 bg-card border-l border-b border-sacred-border rotate-45" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer guardrail — only when expanded */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 6 }}
            transition={{ duration: 0.18 }}
            className="shrink-0 mx-2 mb-3 rounded-lg border border-saffron/10 bg-background/40 p-3"
          >
            <div className="flex items-center gap-1.5 text-saffron mb-1 text-[10px] font-semibold">
              <ShieldAlert className="h-3 w-3" />
              <span className="whitespace-nowrap">OS Guardrails Active</span>
            </div>
            <p className="text-[10px] text-muted-sacred leading-relaxed whitespace-nowrap overflow-hidden">
              Reflective companion, not guru replacement.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Collapsed footer dot */}
      {!expanded && (
        <div className="shrink-0 flex justify-center pb-4">
          <div className="h-1.5 w-1.5 rounded-full bg-saffron/50" title="Guardrails Active" />
        </div>
      )}
    </motion.div>
  );
}
