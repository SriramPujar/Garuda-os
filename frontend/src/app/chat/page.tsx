"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Cpu, User, BookOpen, AlertTriangle } from "lucide-react";
import { getApiUrl } from "@/utils/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  verses?: string[];
}

export default function ChatSpace() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Pranams. I am the Orchestrator for your Garuda Dharma OS. I can assist you with understanding scripture verses, preparing rituals, managing your sadhana, or offering reflections based on Hindu philosophy. How may I support your spiritual journey today?",
      agent: "Orchestrator"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    setErrorMsg("");
    const userQuery = input.trim();
    setInput("");
    
    // Add user message
    const newMessages = [...messages, { role: "user", content: userQuery } as Message];
    setMessages(newMessages);
    setLoading(true);

    try {
      const response = await fetch(`${getApiUrl()}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Send default auth token if login is bypassed locally, we can send a mock header or fetch token
          "Authorization": `Bearer ${localStorage.getItem("token") || ""}`
        },
        body: JSON.stringify({
          query: userQuery,
          history: newMessages.slice(1, -1).map(m => ({ role: m.role, content: m.content }))
        })
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Unauthorized. Please register or register a profile in Settings first.");
        }
        throw new Error(`Server returned status code ${response.status}`);
      }

      const data = await response.json();
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          agent: data.routed_agent,
          verses: data.verses_cited
        }
      ]);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to contact backend. Ensure FastAPI backend is running.");
      // Add a fallback helper message
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: `Hari Om. I am unable to connect to the Garuda Dharma OS backend service at this moment. Please check if your FastAPI backend is running at ${getApiUrl()} or if you need to register a user session in the Settings tab.`,
          agent: "System Fallback"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col bg-card rounded-xl border border-sacred-border overflow-hidden">
      {/* Header Banner */}
      <div className="flex items-center gap-3 bg-background/50 border-b border-sacred-border px-6 py-4">
        <Cpu className="h-5 w-5 text-saffron saffron-glow" />
        <div>
          <h2 className="text-sm font-semibold text-foreground">Orchestrator Consultation Space</h2>
          <p className="text-[11px] text-muted-sacred">Resolving queries through specialized Hindu Wisdom subagents</p>
        </div>
      </div>

      {/* Message logs */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            className={`flex gap-4 max-w-3xl ${msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"}`}
          >
            {/* Avatar bubble */}
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg border font-semibold text-xs shrink-0 ${
              msg.role === "user" 
                ? "bg-saffron/10 text-saffron border-saffron/20" 
                : "bg-background text-muted-sacred border-sacred-border"
            }`}>
              {msg.role === "user" ? <User className="h-4 w-4" /> : "ॐ"}
            </div>

            {/* Content bubble */}
            <div className="space-y-1.5">
              <div className={`rounded-xl px-4 py-3 border text-sm leading-relaxed whitespace-pre-line ${
                msg.role === "user"
                  ? "bg-saffron/5 border-saffron/10 text-foreground"
                  : "bg-background/40 border-sacred-border text-foreground"
              }`}>
                {msg.content}
              </div>

              {/* Message metadata details */}
              {msg.role === "assistant" && msg.agent && (
                <div className="flex items-center gap-3 px-1 text-[10px] text-muted-sacred">
                  <span className="font-medium bg-saffron/10 text-saffron px-1.5 py-0.2 rounded border border-saffron/10">
                    Agent: {msg.agent}
                  </span>
                  {msg.verses && msg.verses.length > 0 && (
                    <span className="flex items-center gap-1 font-medium bg-background border border-sacred-border px-1.5 py-0.2 rounded">
                      <BookOpen className="h-3 w-3 text-saffron" />
                      Cited: {msg.verses.join(", ")}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-4 max-w-3xl mr-auto animate-pulse">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-sacred-border bg-background text-muted-sacred font-semibold text-xs shrink-0">
              ॐ
            </div>
            <div className="rounded-xl px-4 py-3 border border-sacred-border bg-background/20 text-xs text-muted-sacred flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-saffron animate-bounce" />
              <span className="h-1.5 w-1.5 rounded-full bg-saffron animate-bounce [animation-delay:0.2s]" />
              <span className="h-1.5 w-1.5 rounded-full bg-saffron animate-bounce [animation-delay:0.4s]" />
              <span>Orchestrator routing to subagents...</span>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="flex gap-2.5 items-center rounded-lg border border-red-950/40 bg-red-950/10 px-4 py-3 text-xs text-red-400">
            <AlertTriangle className="h-4 w-4" />
            <span>{errorMsg}</span>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </div>

      {/* Input panel form */}
      <form onSubmit={handleSubmit} className="border-t border-sacred-border bg-background/50 p-4 flex gap-3">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question (e.g. 'How do I overcome procrastination using Nishkama Karma?')" 
          className="flex-1 rounded-lg border border-sacred-border bg-card px-4 py-2.5 text-sm text-foreground focus:outline-none focus:border-saffron/40"
        />
        <button 
          type="submit"
          disabled={!input.trim() || loading}
          className="flex items-center justify-center rounded-lg bg-saffron text-background px-4 hover:bg-saffron-light transition-colors disabled:opacity-50 disabled:hover:bg-saffron cursor-pointer"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
