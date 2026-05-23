"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  MessageCircle,
  Flame,
  Music,
  Menu,
  X,
  BookOpen,
  BookOpenCheck,
  Sparkles,
  Calendar,
  Tv,
  Network,
  Settings,
  ShieldAlert,
} from "lucide-react";

const mainNavItems = [
  { name: "Home", href: "/", icon: Home },
  { name: "Chat", href: "/chat", icon: MessageCircle },
  { name: "Sadhana", href: "/sadhana", icon: Flame },
  { name: "Nada", href: "/nada", icon: Music },
];

const secondaryNavItems = [
  { name: "Scriptures", href: "/scriptures", icon: BookOpen },
  { name: "Journal & Reflection", href: "/journal", icon: BookOpenCheck },
  { name: "Rituals & Puja", href: "/rituals", icon: Sparkles },
  { name: "Festivals", href: "/festivals", icon: Calendar },
  { name: "SpiritualTube", href: "/spiritualtube", icon: Tv },
  { name: "Workspace", href: "/workspace", icon: Network },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function BottomNav() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      {/* Bottom Nav Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 h-14 border-t border-sacred-border/60 bg-card/95 backdrop-blur-lg flex items-center justify-around px-2">
        {mainNavItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="flex-1 flex flex-col items-center justify-center py-1">
              <div className={`relative flex flex-col items-center justify-center transition-colors ${isActive ? "text-saffron" : "text-muted-sacred"}`}>
                {isActive && (
                  <motion.div
                    layoutId="activeBottomNavPill"
                    className="absolute -inset-x-3 -inset-y-1 rounded-full bg-saffron/10 border border-saffron/20"
                    transition={{ type: "spring", stiffness: 350, damping: 30 }}
                  />
                )}
                <Icon className="h-4.5 w-4.5 relative z-10" />
                <span className="text-[9px] font-semibold mt-0.5 relative z-10">{item.name}</span>
              </div>
            </Link>
          );
        })}

        {/* More Menu Toggle */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="flex-1 flex flex-col items-center justify-center py-1 cursor-pointer border-none bg-transparent"
        >
          <div className={`flex flex-col items-center justify-center ${menuOpen ? "text-saffron" : "text-muted-sacred"}`}>
            {menuOpen ? <X className="h-4.5 w-4.5" /> : <Menu className="h-4.5 w-4.5" />}
            <span className="text-[9px] font-semibold mt-0.5">More</span>
          </div>
        </button>
      </div>

      {/* Slide-Up Bottom Drawer Sheet */}
      <AnimatePresence>
        {menuOpen && (
          <>
            {/* Backdrop Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.65 }}
              exit={{ opacity: 0 }}
              onClick={() => setMenuOpen(false)}
              className="md:hidden fixed inset-0 z-30 bg-black"
            />

            {/* Bottom Drawer */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="md:hidden fixed bottom-14 left-0 right-0 z-30 max-h-[70vh] overflow-y-auto rounded-t-2xl border-t border-sacred-border bg-card p-5 space-y-4 backdrop-blur-xl shadow-2xl"
            >
              <div className="flex justify-between items-center pb-2 border-b border-sacred-border/40">
                <span className="text-xs font-bold uppercase tracking-widest text-saffron flex items-center gap-1.5">
                  <span className="text-saffron font-bold text-sm">ॐ</span> Workstations & Tools
                </span>
                <button
                  onClick={() => setMenuOpen(false)}
                  className="p-1 rounded-full bg-background border border-sacred-border hover:bg-card-hover"
                >
                  <X className="h-3.5 w-3.5 text-muted-sacred" />
                </button>
              </div>

              {/* Grid Layout of secondary items */}
              <div className="grid grid-cols-3 gap-3.5 py-2">
                {secondaryNavItems.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMenuOpen(false)}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all ${
                        isActive
                          ? "bg-saffron/10 border-saffron/30 text-saffron shadow-sm"
                          : "bg-background/50 border-sacred-border/60 text-muted-sacred hover:bg-card-hover hover:text-foreground"
                      }`}
                    >
                      <Icon className="h-5 w-5 mb-1.5" />
                      <span className="text-[10px] font-semibold leading-tight">{item.name}</span>
                    </Link>
                  );
                })}
              </div>

              {/* Guardrails Info inside sheet */}
              <div className="rounded-lg border border-saffron/10 bg-background/40 p-3 flex items-start gap-2.5 text-[10px] text-muted-sacred">
                <ShieldAlert className="h-4 w-4 text-saffron shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-foreground block">OS Guardrails Active</span>
                  This companion is a reflective tool to support your self-guided practice (Sadhana), not a replacement for traditional gurus.
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
