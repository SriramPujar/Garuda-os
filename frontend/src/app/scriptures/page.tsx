"use client";

import { useState, useEffect } from "react";
import { Search, BookOpen, Bookmark } from "lucide-react";
import { getApiUrl } from "@/utils/api";

export default function ScripturesSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Load default/daily scripture highlights on mount
  useEffect(() => {
    fetchResults("karma");
  }, []);

  const fetchResults = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/scriptures/search?query=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchResults(query);
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex items-center gap-3">
        <BookOpen className="h-6 w-6 text-saffron saffron-glow" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">Semantic Scripture Vault</h2>
          <p className="text-xs text-muted-sacred">Retrieve relevant wisdom from Bhagavad Gita, Upanishads, and Vedanta scriptures</p>
        </div>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3 max-w-xl">
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-sacred-border bg-card px-4 py-2 text-sm text-foreground focus-within:border-saffron/40 transition-colors">
          <Search className="h-4 w-4 text-muted-sacred" />
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search keywords: 'anger', 'breathing', 'peace', 'karma'..." 
            className="flex-1 bg-transparent focus:outline-none"
          />
        </div>
        <button 
          type="submit" 
          disabled={loading}
          className="rounded-lg bg-saffron text-background px-6 text-sm font-medium hover:bg-saffron-light transition-colors cursor-pointer"
        >
          {loading ? "Searching..." : "Query"}
        </button>
      </form>

      {/* Search Result Cards */}
      <div className="space-y-4 max-w-4xl">
        {results.map((verse, idx) => (
          <div key={idx} className="rounded-xl border border-sacred-border bg-card p-6 space-y-4 hover:border-saffron/20 transition-all">
            {/* Header info */}
            <div className="flex justify-between items-center border-b border-sacred-border/60 pb-3">
              <span className="text-xs font-semibold text-saffron uppercase tracking-wider flex items-center gap-1.5">
                <Bookmark className="h-3.5 w-3.5" />
                {verse.scripture} (Chapter {verse.chapter}, Verse {verse.verse})
              </span>
              <span className="text-[10px] uppercase bg-background border border-sacred-border px-2 py-0.5 rounded text-muted-sacred">
                Theme: {verse.theme}
              </span>
            </div>

            {/* Devanagari Sanskrit */}
            <p className="text-center font-serif text-lg text-saffron-light leading-relaxed tracking-wide py-2">
              {verse.sanskrit}
            </p>

            {/* English Translation */}
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold tracking-wider text-muted-sacred">Translation:</span>
              <p className="text-sm text-foreground leading-relaxed">&ldquo;{verse.translation}&rdquo;</p>
            </div>

            {/* Commentary details */}
            {verse.commentary && (
              <div className="rounded bg-background/30 border border-sacred-border/40 p-3.5 text-xs text-muted-sacred leading-relaxed">
                <span className="text-saffron font-medium block mb-1">Dharmic Commentary:</span>
                {verse.commentary}
              </div>
            )}
          </div>
        ))}

        {!loading && results.length === 0 && (
          <p className="text-sm text-muted-sacred italic">No scriptural matches found. Try another query.</p>
        )}
      </div>
    </div>
  );
}
